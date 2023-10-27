from dash.dash_table.Format import Format, Group, Scheme, Symbol, Sign


def money_format(precision: int):
    return Format(
        scheme=Scheme.fixed,
        precision=precision,
        group=Group.yes,
        groups=3,
        group_delimiter=" ",
        decimal_delimiter=".",
        symbol=Symbol.yes,
        symbol_prefix="£",
    )


def percent_format(precision: int):
    return Format(
        scheme=Scheme.percentage,
        precision=precision,
        # group=Group.no,
        # decimal_delimiter=".",
        # symbol=Symbol.yes,
        # symbol_suffix="%",
        sign=Sign.positive,
    )


def conditional_format_percent_change(columns: list[str]) -> list[dict]:
    conditional = []
    for col in columns:
        conditional.append(
            {
                "if": {
                    "filter_query": "{{{col}}} < 0".format(col=col),
                    "column_id": col,
                },
                "color": "tomato",
            }
        )
        conditional.append(
            {
                "if": {
                    "filter_query": "{{{col}}} = 0".format(col=col),
                    "column_id": col,
                },
                "color": "white",
            }
        )
        conditional.append(
            {
                "if": {
                    "filter_query": "{{{col}}} > 0".format(col=col),
                    "column_id": col,
                },
                "color": "green",
            }
        )
    conditional.extend(
        [
            {"if": {"column_id": "commodity"}, "width": "140px"},
            {"if": {"column_id": "commodity"}, "textAlign": "left"},
        ]
    )

    return conditional
