﻿
init -500 python in _compile_build_init:

    from store import config

    _paths = (
        "Translator3000Data/third_party_python_modules/",
        "Translator3000Data/my_python_modules/"
    )
    if renpy.version(True) < (7, 4, 0):
        _paths += ("Translator3000Data/requests_module/",)

    for _path in _paths:
        renpy.add_python_directory(_path)
        config.search_prefixes.append(_path)


init 1 python in _compile_build_init:

    from store import _translator3000

    if _translator3000.VERSION != tuple(map(int, config.version.split('.'))):
        raise Exception(__("Версии сборки и проекта не равны."))

label start:
    scene expression "#888"
    while True:
        menu:
            "Собрать билду.":
                if _translator3000.DEBUG:
                    "Внимание! Билда собирается с включённым режимом дебага."
                $ _build_creator.RPACreator.create_build(build.name)
                "Собрано!"
            "Протестировать.":
                $ _a = renpy.input(__("Фраза в этой строке будет переведена."))
                "[_a]"

    return
