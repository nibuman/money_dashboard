from dash.dash_table.Format import Format, Group, Scheme, Symbol


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
