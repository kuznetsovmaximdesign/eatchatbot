from datetime import date

from nutrition_bot.services import calc


def test_calculate_targets_changes_with_goal():
    maintenance = calc.calculate_targets(
        weight=70,
        height=175,
        age=30,
        gender="м",
        goal="поддержание",
        activity="умеренная",
    )
    cut = calc.calculate_targets(
        weight=70,
        height=175,
        age=30,
        gender="м",
        goal="похудение",
        activity="умеренная",
    )
    bulk = calc.calculate_targets(
        weight=70,
        height=175,
        age=30,
        gender="м",
        goal="набор",
        activity="умеренная",
    )

    assert cut.kcal < maintenance.kcal < bulk.kcal


def test_format_daily_report_includes_markers():
    profile = type(
        "Profile",
        (),
        {
            "norm_kcal": 2000,
            "norm_p": 120,
            "norm_f": 70,
            "norm_c": 250,
        },
    )()
    totals = calc.DailyTotals(date=date(2024, 1, 1), kcal=2100, protein=130, fat=60, carb=200)
    report = calc.format_daily_report(profile, totals)
    assert "📅 Итоги" in report
    assert "💡" in report
    assert "Калории" in report
