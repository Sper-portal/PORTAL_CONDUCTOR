# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.56)

SOS rapido + calculadora ajustada + retoques de pantalla que pidio Juan (17-11-2026):
  - SOS rapido: un toque en el boton rojo -> cuenta atras de 3 s con un boton CANCELAR grande -> el aviso sale solo a los contactos de la app.
    SMS / WhatsApp / Compartir quedan en un bloque cerrado «Otras formas de avisar» (se abre solo si el aviso por la app no es posible).
  - Boton SOS: a la izquierda, debajo del boton MENU (sigue fijo: al bajar la pantalla se queda arriba a la izquierda).
  - Calculadora (precio estimado de Bolt, ajustada con el Excel de 217 viajes): el descuento de los viajes largos tambien se aplica sin demanda y al aeropuerto
    (index.html + OfferAnalyzer.java + ScreenReaderService.java). Tarjetas y tarifas no cambian.
  - Calculadora (pantalla): se quita el cuadro «Resumen del dia»; al lado de «Ultimos viajes · N» sale «Cancelaciones · N» (solo si ese dia hay cancelaciones). Facturacion NO cambia.
  - Cuadros € / hora, € / viaje y € / km: las cantidades de abajo (horas, viajes y km) un 20 % mas grandes y en negrita.
  - Control, «Todas las apps»: el primer circulo (salia vacio) pasa a ser «Total apps»: las horas de todas las apps del dia.

  Cambia www/index.html y 2 archivos Java (no toca manifiesto, camara ni la nube). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v355.py (la v3.55 del SOS completo). Hay que volver a compilar.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNrtXOtuHMl1fpUiNzvdvexpDq8rzagpcCluvI4kEqK8DrASjOrumpkm+zKq7iE5IgkEARIEyI8ADmADhpFg/wQx1vsjcIAA3iABxDfZF0geId"
    "+p6utwqKXktWEEXi05091Vp06d+zl1mhfLwzAS2XKffXGxPOH5GN+WeRLINAxW+WSymkl/NeZhsnrMT/mqn8ark1TmPMLXJJj6eSpXD4ZDIXcT"
    "Hs1eC+nQuGWbLSc8FgTsh7juMxGxQGT+VCR5im/sNOTHgkVcjlKW89gLRcKyMMGjGKtzNmM8YlzIdDIVElPMm4tYtIoIwlxh/8UyK/4Lh8z0nS"
    "hNRo/CzGc7rMc6HbYUc/XBQ0mfJzHbcZke9hcx3cENtub02ApbE937FrsAqNVVQryBRpIyn7DlLxJa/U5LtpeqAJ9uOFvbfQYysrS5dRt7LynS"
    "ogGWfGmzL5YnUy8KfRak+AQJ9QZcttazWYUBLjcG1Tobm31N8ExTPGMmmBFUk0+AFeFRYNDHKKAgj0XOmcePeQ33Q2b2AFyjW7BT8eH3gdSAFT"
    "e4JtZNWt1GKuudt/Dy5ZXN3lsDjnwpRPJM8EDIIyFPQ1/coge5OIcYvfnq81r+33wDRID9aZhBzm8DtUjaVz/6qKVILR62NC7GTKV3NVkGDFSb"
    "JiyajrikR+KUhtptyjBTscpiH63WIj+/rnmTMW3OWb8fdJQ6NHVQOiLLCxXUWixFPpUJe7H8+W10mkjhAxmPZ4K9eDFdX19bf7EMK5BM47UaoI"
    "U7uP3hi+XBTdW/27Lvt9ScYJ6dna2GSSDOnXEeR035OuQJhDLCjo4Ojpi8/nISBqAXSJqnr6bCZhsss9keT3wBdGzI4EEuecaGqYzxAYqTBHL5"
    "5hvLViACAcVJlWw+2X96/QvNijdfPRPZNBaJehBcf80hv7ja45E/jXiQSk6wi3Ww3QQK/uY/2NM339jMn3LolVrs27/+NVtlYwxn8fWXGRtJsE"
    "MAQ//6awlIpCTP05zUejLJsIZZb3uhLqyyDaJ7G7cXieaRuSTTNHdABzk7EpEgrTUNxweWXcwwLOtCD2UsEjnDbWDmTjIngb7uRwIw86MQJi4Z"
    "DcqBBNXUIzsd/en4Ec+yx2GWO5CxHEYjM40kzQUWsCqgFYRiEkbBaO0Gx9zHMj94/uSxafBhLqRIAsMO+OxoGsdczswT25gnPgAX4K4a+qloUT"
    "iYGSevNeazW1kHJWxwj5m4HnIfAgz2Xf8mYZDL6y8ZlzL0yOJGYGBhuAXJw/UvojyMq5uQnwGDgANjn5Paa6ZD6eKUkIESTLjEUhpt0DgT+W6e"
    "A/o0F6YR8Jx3A+FvbG0btrFmWINa00FyH5geHpnETqvT+U62FoqYy6moFLftgLMUsraACrj1aZMKytFc/ypRpIRWFdtyJhHPSYdoQeKSsi5Eoz"
    "AmPwEqPdp/zA73n3128OgA5AMzQJ089bmlKYDxWc5OT90g9Yk7ueOlwazTaV06o5tEgrrm3Cj5T+J4enp5CUCuaxCZDOtCw37lNqk2wMhXIN0r"
    "Z8yzWwjfItwVLXDVtLcarIgn+cyNSNrnOaAeNVFTNzqdMBdx5kQiGeVjS91zsnwWCScIMxBy5kJbEmEMihXxv17qJ9J3z2AA0jOHtEJIYtWglP"
    "c/FDpKbLYqzVps5SgSIRkiI3dDOcoxppI6iBC2BP0SShuVZPlNkEpCcjm7aErKOFCb7HQWbhXsnNCD7hghRHPL46Bt4xK3N4DcmhpomLN0yA5h"
    "tuLJfgIgIjtIHnHIxQlsI6abT6exJ6QZ5g5kUiri6W+ORhlqAJwz6/KyZ+30rGRl5aq5nD92x8FNTU26SYWkQjPB3ApPLdX+GII8rtUDERIQK6"
    "yyaWQTTjD8sba+T+EPIf8EeIAV4T0gMHvjMApMALqqQWMCRWN7MNSA4xo3mGmsJAShtuk8CEwDStP1m0hfiSgTRCKAB0wp4vRUmFZ7anG3mn1V"
    "GW388nnuj02h1TWF+J1xmZhGEfQ20TJsYd1BL5Si/tkFfOpsL5R+hIW1L4VMkssFnHE6ldlz7N9E0GBZV+3RiL8rD2OTmi0CRo55HpBtwGj7o2"
    "6e5sbbgSocnyBoIZs6mUYZ6Qwee2lO5lamiD0eeDuIRB6sejvMLPwPJ0ONjQp/zC2w6AkCI0em0yQwj5xxGgVPstW1Xq9nrRiwsyPch/LNyORy"
    "TwpWBdpkpfMpm3qhrw28wx5jJEQq0zlJSu7tFLhmLL/+bRHQYkZ8/ZvTMOoXdlxHuwnHL1Jp58FqEJ7uGMo0HdKm7rql8PWraSgk5X+NwKuYqe"
    "Ivy2H78SQUrzncD2cqIMbkXFL4BNyMFdMsZOHw0R4WWe90ii+OHxwJH6q50SYLhXS0EUX+jHAr40NC0FZUo6BQO0nE6tOMqcAG6psV8TukwF5E"
    "zaMnR6D7j8c8z3YnEx1EJDpiuC3w7DM+vv6aZfhpkL6maR0FLA1DKQL4yKl88DGYnY3Ts+fhBFqnfUI1xKLfuN1y+QjAcyKijoxVwHODmoiWgX"
    "7NgpIwyEvCnGsPryQpY3DzTEiZSktjSLZAOCdiRo4YxlRI4/KyusHgloWDKIjym0diyKdRDgSrHVxd0RbeC4beKwAoNIbcmwutuAx5N+KeiKCk"
    "kIs+iW9L/9Zr4aAgjU0QZUvGZ9OAAg1C7C5QFbQbAAa1OM1LEqRio15Zy2Rh9zJat2A8DL2IbvUDEBKMVWOcMHANsOaQLoxCJt539pHzk7znki"
    "90kvTMrNEpHTJ3vUXhGShm+y4emJZNjsb1psoJ2XAHkzSzGokkmF3D75pqRfKjDza2ekUk1pZgyGUcZgiotQTTT9u8KaUWkGPFC6ktVED+Om3G"
    "Er8D6hURgDxHAuSo/OxgCIGYTLqGBTmFJ6fg5chRZN2LQv+k02lemdz2rLe5vy1YHu30NBWuGhTjpAlxKpFcXQAv+uYuFV8G2huCWcW8Kgz6A6"
    "JaUCjL3QsQrT9Ecjp+CInO+8k0ikBLsLy4a6QnRt/wpplPESGgSNk3jKtCct8fgk3E6A85IpSrpv1MyhhrvOIaD8D5HAZcRSvui2Xso+uFI9pP"
    "Fyb0xTLTQkGP4uzF8s7//vM//krZd+hxShprIlRaMawHWYwYYMdYEZlv+k6h35kT84l57u6cO8nl5bkzsZzjNATVbJgx8kcItUr3DB8ClpD9rR"
    "yxci2pCpN9Gebpg1W9CjyUQnvHGDS2AjVu7SObekD4QNno0hfZMP3kzfC7X/qWQilqnOGd9jl4bZ7boeXuXHwXoUZUtmuS6oyXVyGujJVwxVCk"
    "++mva6eogkwiVkWaFaPe15WOMXV8+ZY9euk5IO9e/zYhtc9DkYg5N42LYciT17zwpW/bSMDlSXMf/nAE6P/zn3/Pdq//jZM1r0DPsUAp2XfRaR"
    "58NuZSYIFv//bnbA/JB5d5KL/9q38pZGk/CkeCXPVITicpm7IUsQPJyC1i8F3Ln42R87W2ByBapP+JPY44MnhK4NbW1gsEjmrLqioaQSr7KiAs"
    "YqZIzXkbNvPsGiIJx4qtaDPjkSrL1AGmw55jERV3FSu9+QpBUUhxksOe6opOEiYjYruKliDS0zyNr7/MQ78OREsno+19egKxc5eW4GJAwwNl49"
    "QX07KUrThAtoTnhRm9vFxSM8gHpifPXH3RLp+EtdMhJdMRIQmioMgoC71I2GQsViup15vlXkil+uyPj2uwj2qj1m1oEWm6XhMfuoNrFQqJ8wmV"
    "MgOl9WZJ1IcGlVJgopUxNixlDRYHwswEuezKSkAZKNFpQPr2Z/8OQN/+7L+Mlr1QyJOxeKspXLhkyw5Ws8NAT32idzdPghZOLMUHsCp2VlHyT5"
    "7mT57m/6+nWaQ1C2z9HlBs6TRLaxTspmFqGvn9BXaVbGeRjeOpzz2uHrXSV5tGnaYqKyCw4FGZvTbdgooGtVv4S7ddOHAvVMGgv6VqP28fs2E3"
    "ISWem8cTB5lolquiG1WbE8+C5DhSTCLuix+H+ZhuXdWw32HWgMJ0PG04MHJNS66L5FEMw4TKAtW9paXavx05ZVJQh/FlrpzN8453z0hU/uE3bJ"
    "cMJJVpby1/UPr6gKqQlcEEh/cCsoIr3PED0jR6vMMyErdGhWjRsmBe1w+UAv/iX9Xq6aJ8+Y4LFlo4t0gWYyx8pK6yKHlaXMMJEWbAxQf6cJeq"
    "twLyqvP7GzKlSend1MpR2tRDyrmQ6JIh0e5uxivVKme2ButKAKlRXZwqNZGouGBFomEx6xZY3/7yZ2xv9+ne/uPdZzeWf3fEy90r91smp/WCdB"
    "QTCS4/o0rOKY9MP3huDfDL7Q0Odx2VyNGhjRo7mPBDHiZIvpWKvAfII8eP0kyoAgZBUaiZ3FFVKgIDbv6EqkV0FG08pJgE1kPZ7tFUYmefFs9I"
    "0hBDZdSIgBgK/p3kAAPFuToUS3Xhy1Anst/LAvNAqicPjcY4xgsfpM8mqzPF2xEsanOgo+x0pF7DuqCTiWOXkmllV45dfsbDnBXPlY8W57lznK"
    "VJy2wUp2MX6YlOrm01vm8edzrHBezLSwMhjaHLebcuixw+B8NocfpWHLLMrV/NrBAigZmqs5YGUt//DkzCyXU3e5sP28zoq71VpcaqUAKhC9zh"
    "NPHpLMh8q9Brqh8ePVdfdKnj+4DzIln9qDqh++9FuYmWGQgepQawb+ac9yQPfP0llSIFyQ/54yC1HpI1TFKVy7BVdks246jOlMLpNHdQhMNLmW"
    "dWh6uK8GWgvHS4O3darW7DOuRA+MYj7Tgzt7Qe5fhMnf6OhX9iXF6qC5KH8nsGD4icsbwkd2ksWlU9DdLGU+SMWEqKrNPRn04gqDkp2+lVdwA9"
    "3+npWHJui1eDZreORl4WskrJ3KeJecEVrfoGCCpzw6Zt9wkpm1pc+vGMTvZMy56MgRcuD+kTMl2fxHl0bsuRcEJ21Lpe64QvRVxRDo2zEbQsPX"
    "mI39VGkFn98m/YIZb0eMF33qfjGAq5ElitlJ2GHpkvkdSZum5corp1UcB2jH7dIUSqjpS7MjF66yP3iEqHcaejSXAo0zjMhCMR6Zhf6GfYaiLO"
    "ykemzNydTOTPw1ik09w0kSrIzLxQdb4cEbx9n069rJfqfH/U6SyNSI07nZET8XxJIaAu0kRfWMBq1DAIraw+oj4NRYYoEqe8HRcwE0l/JooCc4"
    "YoVFolXfX2Jp77vtwk7JF6X0w8wtudTOhjQFdpoq7ShK6479MVPq7aS88J1cT7/YoHcuDJBNnvjeAJJpLolDRuqTPDMeiWBiqiIsJF3KKM+T2l"
    "TKnUA8pWJ7mOBSeB35WciiU7JIMPVDtD/eh0Y2u762eUWtd2kpJDL6W4h9q+3n4amarDyB+pMzOq7tCxNBPnYLaa5+sOGlV3SQPq4qISAwEYkN"
    "mlPggepZIqXphHNhmiNKS2Nd3S9wFi2U+5Bwc5zPunXJrdLqVRkX1/cm4t6Y4anuQDGY7GeZ/qXY2beTppzMnt7fakKw1eBUXMKYsYF0WrR586"
    "PRYPcai0UY3zotQ/WTyw67VHDc7CIB/313q9DwckaV2OHDPpU5eXkAMvlchG+muTcwrAw4DJkcfN9a0tu/xxNrasgcf9k5E64Ib68ARxPdKYfO"
    "AjZpf9D4bDYQEIbA/CadZf25ycI4IMyM7319ZxATc3ChOggZWo5yPJ+/d6Pba2hWvlU+1sluUi7k5DG6lO1oWbD4cDfyozLDFJQxpT7Bge75P0"
    "HFumJOWCYHWz8LXor4HWi4awD8rspDF4cxtYqcszoRgJ0zWI4Iu6Y329VuLcYzS0sddTGBPoU1SQMg6DIBI3F87iJm4bgJFOoIT5rO/cu1cA75"
    "K8ELFaK4PmV23VmBSNlXR+z5UelIlYn1VK8earVhnyzTcUF4SceRGCdeh6SjWn4oJ0R4pRxBtKNeIJp1YAAo7Nql6BWiV2yYYe+ZLpbMPxHIFF"
    "LhqioYhT0OmegCfotYlSTKzyoothJM77awz/SDprYq03xWedREYJ1JyMEVduWd3fXr+3fg8TzrvZGIHTGZi4WYDRIt6z6Z+zCeGGd4RsdTNiDt"
    "ZztpQUNanf6Mm7W8fVjxY2XBEl271Rjm7FUYToBkhHtL+S6VnDpCgp66o2sT6lKyQqg+NplofDWdfXjqNP2EP3RX4mRDIY8YlStav5BZnqdrqY"
    "l/uCbGJr895mMFCVbkUPAYt0Jvlkjh5lC23dP2sX33VH9qy4OonJi2d0jJ6HAQ9EVpliqkqy9R77kFENuGi8pWYHZFRiJEOYciIXddoy6j1kHx"
    "Q7ZY4YDmHyReJj91xiS9nUa2oazE2Des2twuI0nrRVbn2rZaVb7E/pyDqir9QPHFDtHj+6J7jP/HBhrzB5Y0VX7GsYHlPdOAtFjDSR4pZICK1a"
    "KjsC9K6vOpQyVt2IBVjnO7qRian6n33X0d5FaWvWGjtGEhJ6YUS31ddINB6CSN5JmHeVkxiGEdZQUgETTMZ+jy5aJKp58057uCgt6dbQGw5/R4"
    "jeXaA5Ud4Qn/fBdYtve/e2vkfoFd49b2240cb7waoKmBAc3YiqKHS6ETZV9psiJ5NEzSIJowX8m41dP/zR0fODWwIqXU30uSd8IbnDdtX7Eogl"
    "XusKb+WFsnBE3R7N0Wxmq8C16ieFBmdC14opxtJ9Zqqd6xVids4WNp7VOsKpLyilfrOkVEC7boZOExthA50gkbXZJWsoMh3r1vuxEOgVXdUiww"
    "JJc6H5vZIumnO5MgI5JvkQKT5dlQ+Rc+RmeaJUP242yeqpw7rRZyTKDv5PZp8FpqFDTEPlSUvDsr2mOTl77Q6ddDhEuvVjiuAuL7d6dq7rNZFO"
    "5ZrD43qt+f7WcSAhfcm0C7Pe7nNF6gfE6BBgmovgiKTOjK2y8XjJLVqPrQtFCDembXxCzhZ+ci+CCc6fYRFT7UI6KtCkztnclQ64kKfxyvYgwg"
    "VF0ivliG722lpdH9Q9sAR8HPRu3wDVS5yxehtJUwyjNU5jz8X329AqkLCjMHbHXncTK9PsfAc3rNxVXZsxPzcrbNdpqHV1pfLQjygtaAq4OmaC"
    "kjKz1IOMxdMZibrqBM2U2sFp0jsHPNIqpRrQ6JwKuii1qiKIUdJWsYHKWyob1nt6F0LoKa/c8dtY86rJmlcOQs6Vj8GXV5ov97Hfhcjk7j2Mun"
    "/VEjN+/rwm3D27bPYMk0TIHyhfenm53etZoHX3Xi1sJbXDxCQQdgNEo3k2tyyEYzX8zebDyKrBDYsWeSjHoURmJPOZaRQpF9L8FWNyDgK9ZVRk"
    "2FExqmiCrosQ1eFepfBSvDJVA/oS1N0ilcedKfi+m4Sxajn/VFIlAWqkm6rrUyoYbLd1dXl5cTVo3aHU7ZCOl1zMHzSmIwDep+ZKat4WoC/Mhg"
    "8zCNyxvH0x4VkWngpd0PD5BCZEXxTVqFuhICJBoKSgWINbR6WSpEjtDsKdjDChYR4bVSBCZh0s/65lo5QHLRiKrIM5SJs1pEoPbsJ6dPCkKJk8"
    "BlQRFJspX1UAqwo0nkz1Fg48qhsLOfdKi0XVrfkxhIflpPrKbI23L3jZpphpwlfXn4YR0oj+F4Y6uDHs5vsxL6+sOQFbuPcN7H3+3hqRloqXlk"
    "kfCA5UTLAoOihrLuUhQ/02MNVHl2KOXzwECU7iHbd8F7jTiXfWVtQbg+r9AUf18x4knY44tcTp0Tg9S1xxOlDH8vAMvluDHUh+5uLnI3OtS4+o"
    "6d2qDhsWLN9c+HtbThvrd36VGTZYU+pxnai1XwKu3symd5P3Dp5WL5bSy7xJ8+3exnvXC1/t1aGRPhFf+IopM9UnTZzCXcTI1G1mGEUb8pjPrL"
    "IvnQI7T/Ji9XBI3kUiVtVH9a23xHXZtMKCYhxizZ32a9/+ojP1as+9GK9fsLX/SAlTMlqN069McKTE+s3A1l8EiG6QpvGabkG+94FSYqDLw0SS"
    "x0g+XeHuqNe8/B3Sv4fGnd4P/vbvfmrUXQt3gbVgfnkOsmI88KqTZu910UD0+W0koDcyDMWylXbTAKaOw4TaTPaTt1PRZp+kyJiyqaDEgBOzYV"
    "2LVgbdL6JyBkhYPI3yUJFYNmTKYY/1EZp+pb6WNfhjlWpQaZP2jiBNFxyacIojuJKlpipnr21AOlUXVhByXfEud2AzxA3lH1wAJH+sWKxbqlJk"
    "JchQboh12Y1QnMDcgcjvSdh30dI/SsKv3Up4dbt4D2atR3/AgpLVLVXb3KabSXqKVFHZg9+FRUoTTk7N25QPjpw0ZiVVyrViAGGg0FAo3XcwB+"
    "Eus9TK+8dIdyOoKB6lozDgRTNCw7oSATaIADMqmCGEbrK7zzbs3ib9wZANdv1z1rPvbeMC49TF2hb9wYuP7fV1VZEz6WtPfZUiSJNA0KHyoJAD"
    "xdGMs3V762M1BlM37e0N+j6gV6fDTJ28rW9hNy7W3d7WjxIBLNd69n01zSFyfP7Z7g/3j9jj3Wd/TkUJzcBUMVS/wq/K10oi4uuvKYomO96ikK"
    "6SQS5D/Z6UUlKTzLxmNNEpq2sS3+Wx5skKf/kHJP1Av3oOscZOmn+2gl67LWSy3qUi/P17Bc+27N478Wzd3rydZ9C4mmf37Y11zbKXL69eXv0f"
    "MVmH/w=="
)
SHA = "3ab3841637c456207038ed76af76903825172b1b84545052d10b5d817117ecc9"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.55';"
V_NEW = "const APP_VERSION='v3.56';"


def fin(msg):
    raise SystemExit(msg)


if not os.path.exists(HT):
    try:
        os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
    except OSError:
        pass
try:
    raw = zlib.decompress(base64.b64decode(PAYLOAD)).decode('utf-8')
    ok_sum = hashlib.sha256(raw.encode('utf-8')).hexdigest() == SHA
    PAY = json.loads(raw) if ok_sum else None
except Exception:
    ok_sum = False
if not ok_sum:
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v356.py. No se ha cambiado nada.')

RES = []


def say(part, state, text):
    RES.append((part, state, text))


def read(path):
    if not os.path.exists(path):
        return None, 'no encuentro ' + path + ' (ejecuta el parche desde la carpeta portal)'
    with open(path, encoding='utf-8', newline='') as fh:
        t = fh.read()
    if '\r\n' in t:
        return None, path + ' tiene finales de linea de Windows; este parche espera los de Linux'
    return t, None


def write_atomic(path, text):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.tmp')
    os.close(fd)
    try:
        with open(tmp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def write_atomic_bytes(path, data):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.tmp')
    os.close(fd)
    try:
        with open(tmp, 'wb') as fh:
            fh.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def short(t, n=70):
    t = ' '.join(t.split())
    return t if len(t) <= n else t[:n] + '...'


def part_file(entry, extra_version):
    """Devuelve el texto nuevo del archivo, o None si no hay que escribirlo (ya estaba, o no se puede)."""
    path, name, edits = entry['path'], entry['name'], entry['edits']
    if entry.get('optional') and not os.path.exists(path):
        say(name, 'ya', 'este archivo no existe en esta copia (no es tu repo completo): se salta')
        return None
    s0, err = read(path)
    if s0 is None:
        say(name, 'no', err)
        return None
    st = []
    for i, ed in enumerate(edits):
        old, new = ed[0], ed[1]
        cn = s0.count(new)
        co = s0.count(old)
        if len(ed) > 2 and ed[2] not in s0 and cn == 0 and co == 0:
            st.append('S')                 # no aplica: el archivo no tiene el modulo (p. ej. sin odometro); se salta
        elif cn == 1:
            st.append('A')                 # ya aplicada
        elif cn == 0 and co == 1:
            st.append('P')                 # pendiente
        else:
            st.append(('?', i, co, cn))
    bad = [x for x in st if isinstance(x, tuple)]
    if bad:
        i = bad[0][1]
        co, cn = bad[0][2], bad[0][3]
        if cn > 1 or co > 1:
            say(name, 'no', 'el trozo %d de %d aparece repetido en %s (%s); no toco nada' % (i + 1, len(edits), path, short(edits[i][0])))
        else:
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.55 que espero (¿has pasado v355.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
        return None
    if all(x in ('A', 'S') for x in st):
        say(name, 'ya', 'ya estaba aplicado')
        return None
    if any(x == 'A' for x in st):
        say(name, 'no', 'esta a medias (%d de %d trozos ya estan y el resto no); no toco nada. Mandame una captura.' % (st.count('A'), len(st)))
        return None
    s = s0
    for i, ed in enumerate(edits):
        old, new = ed[0], ed[1]
        if st[i] == 'S':
            continue
        if s.count(old) != 1:
            say(name, 'no', 'el trozo %d de %d ha dejado de ser unico mientras lo aplicaba (%s); no toco nada' % (i + 1, len(edits), short(old)))
            return None
        s = s.replace(old, new, 1)
    say(name, 'ok', 'aplicado (%d cambios)' % (len(edits) - st.count('S')))
    return s


def part_create(entry):
    """Archivo nuevo: se crea si no existe; si ya esta igual, ya estaba; si existe distinto, no se toca."""
    path, name, text = entry['path'], entry['name'], entry['create']
    if os.path.exists(path):
        cur, err = read(path)
        if cur is None:
            say(name, 'no', err)
        elif cur == text:
            say(name, 'ya', 'ya estaba')
        else:
            say(name, 'no', 'ya existe %s y es distinto; no lo toco (¿tenias otra version de este archivo?)' % path)
        return None
    say(name, 'ok', 'creado')
    return text


def part_asset(entry):
    """Imagen (archivo binario): si ya es igual, ya estaba; si no, se reemplaza (el cartel de arriba)."""
    path, name = entry['path'], entry['name']
    data = base64.b64decode(entry['b64'])
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        say(name, 'no', 'la imagen incluida en este parche esta danada; no toco nada')
        return None
    cur = None
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            cur = fh.read()
    if cur == data:
        say(name, 'ya', 'ya estaba')
        return None
    say(name, 'ok', 'reemplazado' if cur is not None else 'creado')
    return data


def part_json(entry):
    """JSON (package.json): anade las claves que faltan leyendo el JSON, asi no depende de como este escrito. Si ya estan, no toca nada."""
    path, name, ops = entry['path'], entry['name'], entry['json']
    s0, err = read(path)
    if s0 is None:
        say(name, 'no', err)
        return None
    try:
        obj = json.loads(s0)
    except Exception:
        obj = None
    if not isinstance(obj, dict):
        say(name, 'no', path + ' no se puede leer como JSON; no lo toco')
        return None
    pend = 0
    for keys, val in ops:
        d = obj
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
            if not isinstance(d, dict):
                say(name, 'no', 'en %s «%s» no es lo que espero; no lo toco' % (path, k))
                return None
        if keys[-1] not in d:
            d[keys[-1]] = val
            pend += 1
    if not pend:
        say(name, 'ya', 'ya estaba aplicado')
        return None
    m = re.search(r'^([ \t]+)"', s0, re.M)
    out = json.dumps(obj, indent=(m.group(1) if m else '  '), ensure_ascii=False) + ('\n' if s0.endswith('\n') else '')
    say(name, 'ok', 'aplicado (%d cambios)' % pend)
    return out


def part_version(base_text, newer_ok=False):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.56')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 56:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.55 -> v3.56')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.55 (esperaba const APP_VERSION=\'v3.55\'). Pasa v355.py primero y luego este. No toco nada.')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
writes = {}
html_text = None
for entry in PAY['files']:
    if 'b64' in entry:
        out = part_asset(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
    if 'json' in entry:
        out = part_json(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
    if 'create' in entry:
        out = part_create(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
    out = part_file(entry, False)
    if out is not None:
        writes[entry['path']] = out
    if entry['path'] == HT and out is not None:
        html_text = out
base = html_text
if base is None and HT not in writes:
    base, _e = read(HT)
nv = part_version(base, newer_ok=not writes)
if nv is not None:
    writes[HT] = nv
if any(r[1] == 'no' for r in RES):
    writes = {}   # si una parte no se puede aplicar, no se toca nada (ni siquiera el numero de version)
for path, text in writes.items():
    try:
        (write_atomic_bytes if isinstance(text, bytes) else write_atomic)(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.56:')
bad = 0
for part, state, text in RES:
    icon = {'ok': 'OK ', 'ya': 'ya ', 'no': 'NO '}[state]
    if state == 'no':
        bad += 1
    print('  ' + icon + part + ': ' + text.replace('\n', '\n      '))
changed = list(writes.keys())
if changed:
    print('Archivos cambiados: ' + ', '.join(changed))
else:
    print('No se ha cambiado ningun archivo.')
if bad:
    print('RESULTADO: hay partes sin aplicar (las lineas «NO» de arriba). No se ha tocado nada. Haz una captura de esto y mandamela.')
    raise SystemExit(1)
print('RESULTADO: todo aplicado o ya estaba' + (' (hay que volver a compilar la APK)' if changed else ''))
