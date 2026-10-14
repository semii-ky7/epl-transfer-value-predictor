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
