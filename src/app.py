import streamlit as st

from predict import PlayerNotFoundError, euros, find_player, load_model, load_table, predict_values

st.set_page_config(page_title="EPL Transfer Value Predictor", page_icon="⚽")


# Cached so the model and table load once, not on every search
@st.cache_resource
def get_model():
    return load_model()


@st.cache_data
def get_table():
    return load_table()


def season_label(season):
    """2025 -> '2025/26'"""
    return f"{season}/{str(season + 1)[-2:]}"


model = get_model()
table = get_table()

st.title("⚽ EPL Transfer Value Predictor")
st.write(
    "A linear regression model trained on 4,232 Premier League player-seasons "
    "(2012/13 to 2025/26) predicts a player's market value from age, minutes, goals, "
    "assists, height and position. Search for a player to compare its verdict with "
    "Transfermarkt's."
)

name = st.text_input("Search for a player", placeholder="e.g. Saka, Haaland, Cole Palmer")

if name:
    try:
        rows = find_player(name, table)
    except PlayerNotFoundError as err:
        st.error(str(err))
    else:
        result = predict_values(rows, model)
        player = result["name"].iloc[0]
        if player.lower() != name.strip().lower():
            st.info(f"Showing results for **{player}**")

        latest = result.iloc[-1]
        st.subheader(f"{player} — {season_label(latest['season'])}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Transfermarkt value", euros(latest["market_value"]))
        col2.metric("Model's prediction", euros(latest["predicted"]))
        # The model "under-values" a player when its prediction is below the real value
        verdict = "Under-valued" if latest["gap"] < 0 else "Over-valued"
        col3.metric("Model's verdict", verdict)
        st.caption(f"The model's prediction is {euros(abs(latest['gap']))} "
                   f"{'below' if latest['gap'] < 0 else 'above'} Transfermarkt's value.")

        st.write("**Actual vs predicted value by season (€m)**")
        chart = result.assign(season=result["season"].map(season_label)).set_index("season")
        chart = chart[["market_value", "predicted"]] / 1_000_000
        chart.columns = ["Transfermarkt", "Model"]
        st.line_chart(chart, color=["#e67e22", "#2e86c1"])

        st.write("**Every season**")
        seasons = result.assign(season=result["season"].map(season_label))
        seasons = seasons[["season", "age", "goals", "assists", "market_value", "predicted"]]
        seasons.columns = ["Season", "Age", "Goals", "Assists", "Transfermarkt", "Predicted"]
        st.dataframe(
            seasons.style.format({"Age": "{:.0f}", "Transfermarkt": euros, "Predicted": euros}),
            hide_index=True,
            use_container_width=True,
        )

st.divider()
with st.expander("How the model works, and where it goes wrong"):
    st.markdown(
        "- **Data:** Transfermarkt's public dataset. Outfield players only, with at least 900 "
        "Premier League minutes in a season. Value is the last Transfermarkt valuation of each season.\n"
        "- **Model:** linear regression on the *log* of market value, so each feature changes value "
        "by a percentage rather than a fixed number of euros.\n"
        "- **Accuracy on 847 unseen player-seasons:** typical error €5.4m, average error €9.5m.\n"
        "- **Biggest driver:** age. Each extra year costs about 12% of value, more than a goal adds (+7%).\n"
        "- **Known weaknesses:** it over-values cheap players, under-values stars (€100m+ players come out "
        "around €40–55m), and over-reacts to one exceptional season because percentages compound "
        "(30 goals ≈ 7.6× the value). It can't see club, contract length, potential or reputation."
    )
    st.image("charts/feature_effects.png", caption="What moves a player's value, all else equal")
    st.image("charts/residuals.png", caption="Where the model misprices")
