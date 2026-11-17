# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.58)

1) «Cambio el trayecto o el precio» (pedido de Juan, 17-11-2026):
   - En el detalle de cada viaje (pestañas Calculadora y Albaran) sale una casilla «¿Cambio el trayecto o el precio?» con el motivo:
     cambio el destino / parada extra o ruta distinta / recogida en otro sitio / cambio el precio / otro motivo. Se guarda con el viaje.
   - En la lista, el viaje marcado lleva un ⚠. Esos viajes no se usan para ajustar la calculadora (ya no son comparables).
   - En el CSV hay dos columnas nuevas al final: «Cambio de trayecto o precio» y «Ajuste de la tarjeta %».

2) Tabla «Ajuste por distancia» (Ajustes > Estimacion de Bolt > Demanda y viajes largos), TODA editable:
   - Tramos de km (el primero siempre desde 0; hasta 8), un porcentaje por tramo, en cada zona (baja, media, alta) y con / sin demanda.
   - Sustituye al «ajuste fino de la demanda» (lo que tenias puesto pasa a la columna «con demanda») y al descuento fijo de viajes largos
     para el Bolt normal. Aeropuerto y Comfort / XL / Premium / Child Seat siguen con la regla de viajes largos de siempre.
   - Valores de fabrica PROVISIONALES (los afinamos con tus viajes del mes): +2 % de 0 a 3 km, +2 % (media +6 %) de 3 a 6, -2 % de 6 a 10, -7 % de 10 a 15, -16 % de 15 a 25, -18 % desde 25.
   - La pagina y el aviso de Java calculan IGUAL. El aviso dice «Ajuste por distancia: -7 %» cuando se aplica.

3) Control > «Todas las apps»: las letras de los circulos un pelin mas pequenas, se reajustan solas al cambiar el tamano de la ventana
   (pantalla dividida) y, si aun asi no caben, las horas pasan a formato corto (11:52 h).

4) Horas entre movil y tablet: los tramos se unen UNO A UNO (antes, si un aparato tenia algo ese dia, pisaba todo el dia del otro y se perdian tramos).
   Los tramos borrados a proposito no vuelven, y una jornada en curso no la borra el otro aparato ni se reabre una ya cerrada.

  Cambia www/index.html y tres archivos de Java (OfferAnalyzer, BoltConfig y ScreenReaderService). No toca manifiesto, camara ni la nube.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v357.py (la v3.57). Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNrlfcty40iS4K9A6ikBKEEQqUxlZYECNVlSdVd158tKOTljLWlqgkBQhIgHFwCpB5OXPaztdfcyZnPY3T621fZhrA9r1n1os9Sf9BfsJ6y7Rw"
    "QQAEkpsyurZ8a2rFIEA/HwV3i4e3gE55vDKObFpmeczjcnrBzB0yZLwzyLwl02mewWebCbsCjdvWQzthtkye4ky0sWw2MaToMyy3dfDYc8f5ay"
    "+OaW5y7W23SMzZQlHDt7NouKzAi58VUWl54R3P0mDqZxZkB7I2ZGyQbwF16HUVGyNIiYYS13aGOPPIxKgvR0czIdxFFghBl8coMX5c+jlBu+0e"
    "lhxaW3z8JLeml82H+7u8bskbv/1DPY5bQouQEoa/CxCfTOwsywPnMIjSK6SDPP2DaK6YAbN8aOMWCXTGCXX/KS2Wep6vseyM8do8JskGUxZ6nB"
    "ZzwtX6VQocynXMdO1UC46grLKAgCn20+W4HK2aZhFRkwA3ljpFmesNgBdFKD8TybTHleZnYPEGYXLGSewWPgVBFMAabMGEaXxNdZxC55AdjmF1"
    "mBBUXEk0nO1+B8ek7jH03LAoDGx2M+xG+W3buXJWebMHbIEeZxYuNAwAQgcc6SrIegTfIoAbCBqEZn7eBy+Jf12G9ZDGM74mu7uCcH/4wId5ul"
    "IJ4dYq9jdI0ERBIe9gwWA5OB8wSMRxQMeQLziBm7JCLy2xJY6/isy4KUFYArWCPibLV8/0VyvFZW6/EFcHk0Y9An9FZCpa+LEvgRBxaK0tHwwg"
    "icCrnpxFGdjJPqMYnS6jnDGf9iGpeOcVLmUXphsHH1yGe2MUekdz///AOlGoRjyAY5oGdYr7979fbbk29fvXz23FPCGoK47APXjO6TnW53Z6+z"
    "96RnFEDIYQQcRlpAhQQqAldApGzX+PZiCtX/05Qbx9+evPn+bQe4jU/HOBaAAlMEmrrG57uCfpIsDZmvBN2YGzkvp3lqpPyqqjPvOMYjx3gCkg"
    "VP3X0QrP1Fz1icpSu7rDsVomrMa86t6B36n+9Bl46xg/++gH/dJ/jn6cIx8M2TtW9WtVn0hICJqSAnAk4DAUQFtMazzySpHuDdhOUM5jDoEhQW"
    "XjAx7UTbnAfZRQTT6oa4tNuYalZUMQk7fB2UDebYa7ijKuuiG6UlDssbglupXJ40qB0NDStwa63mG+k0jm3FhU5Pq4r9wizCvrHir7//5ttffG"
    "Mcgg7xDKsuff7q76GwA4VdW2uu8b5EVcUTqCWGPoa64ullrwlaqSAy3r0zytPb8wchjMJrmul16RCYZOErqWgujQOjRtmNeXpRjqB4e9umMceJ"
    "0fe1GqeX57bs9rK3JKf44oBAkz0BVvjtFF6cA14Kkkqq/trKhzRekwm1PqzRqdqcjLIrVOZnm2ebvbagxFl6cYyN+8DgrS1jI2H4oUiGr3+FAl"
    "Zr8CceSXumS7uDyw1LBhFPUZHVC3Y9XD2kWl5gGD6TNAaNAQDYGrR81ms25jHoxLnCtIa8Z+TsCkrw7+eG1QWLh+rsgubquB2blJbqZIGqew3t"
    "nGrp+lgiSrMHyceiHD8DVn6bhvwaXsKjDQLVaRDxA2yh+8wgWNWhUVRObzjSe9kOYqAKwRCBAUC4ooRV3KF6rElZSYdS2huofUBmAxc1wK+iNH"
    "RIWEEijK7bAcuyy3e+tHvLrC0RTcL+R/FYdLXhC5IJnpS9egRbcWynXOL9NmCxmvF13/8fCj2pDO7KbkLqgAuYaFQan2y5pUqC/vB3ZQvqOHfB"
    "dTgWzUR76mpFsUFlwgOirqGHc1zY/1J3j3Rslg6ji4d8vZijNwRrch6ydb5eq7e2o1dz0SeNbiXuBS+ts01ZfLZpO7Xs20SEj23TZD+YHwUHEp"
    "YWTMDA7mkKRJAevu386P+MGYvBjAmiLCXL9pP0+ZB6IyTs2i57npGtNESzDeZZmiFU4NBNeTwDfQYT1cqMJueUVV1ERgwWGvk7hWqZgoV1ApNV"
    "1BZ8R7NMeB/kGzKwpwvQpc3eblDbGiM2AImYpoCB9FfAGs+kCaccKKDWhIFNSGAFWTxNUkRZ97E2RROEDgZF47HQTUPU78jfdbZhy7aYwdTQhO"
    "IFmxyIFcoxXg0ueVD2DRCUZsiiMkMaZmK1aClfXbcZWz20/GJp2K2rpnxVZQneX62GaBUyIbRO2KSaNNgWZozdWoHD2oicr1zahqjQBvXkA15y"
    "mnmw6O/so4PT6axa0YZyGaoszlthcd7COvQIPtDCrN5F4l1UWaPHtQ0JxVC3OUDNhmMyL8EUBiKUIzdh1xZBJb5FqVV9ybNpGloWrXTNtkrzq3"
    "VwWJfsgN0OxfANvmApFLaxDdyhiv00XwirWCtcrBQi0m2hJG8m1BoKlj6O4CqYIMgNWTUAoYLKLYZuWFApSkld8GxoPIdhbHsZFiw/OOwbMfRo"
    "yS82DNByIRDA2C2iW261R0qBW130RVJYi5+uGKJymgMxNTQ3Nj1f5ZRoYpAKtreFUtIhI6iQDNEq2dsAfaeR4JjGXEUETc5nSAdLVjUy2xXlMN"
    "emTdTVIKKqGxUv2UsLvAsgRFX0LSyEaVRyWT4j644e+sYeitJKSLDXCOdjB/ymGc0fcJqgsU8UPI1QHM/XNBY1cCLM7pM4qaWwts4BUJ2xtNiB"
    "X7djqDI/24xRTZ9tJuJjdLapogWTrIhwzRMe8D2xtPbwL5ti8Ag8YF3dtV+tkJEVaqQlI6u04W0m1aGYPLdjmPorJjKBSJ61CG7CxMSW0u0+FB"
    "8e9CanoJis6eqOjj+io3C5o8X9vnIzCgv9q6khgh5pgyxVZXbPNNQ1QtZWIQBzrSUyAB0x+MA5zIRcxijRhDhY8vhe6RXoG1cYNaHrpWUfZorX"
    "UKsy0MAeCCRI3xNJ8yzPrRr9BlVEra+mURzy3BhI0jRKgTWnTR3bRpS1sWKNdQs8EDGtyV0ZuGCcc1iGTMeEdb76mlpII7vpe0hc6zbnpu2WmY"
    "CvUknrSED2jmhJBk8L2Q8zdT5cL9RtKnjh7dmZNDzg05vjX1jf8BloqqqpldButaPlrVVXMbTWZbb9YUqiOUHbMGpDCNVQv69BT++H5uXy9K4V"
    "it3GLry/s+N1nR03OjMXpr2K9Fp5HcH91P4OeVEttGZttI5+/ovv33793RJzJ6Lmo/0uTi/0nT5NTzUxNNkfLHuAP8p1PglyztPvOIOpdMLzWR"
    "TwB33ou9+lnBnvf1jl1L3/o2Gt67PtSa+YXkGbVJepVUUQbOqg3YqFl+saPQsvl6X14UFIGlDV1bGLvgh3KUV2tvkWd23EDqMH+oqDGIHdUHDj"
    "7Gy6t9fdA5dvG8Q96Wo9QwkUf3a2SUKCA5A1zwZFDe7ySKuo7BnU/yQo65a6UDSt258OjZbsXV1d7UYY8HRHZRLrIvQavGwWxwD4+x/e/+kI42"
    "V3v8cdLXDXb2Ctz2Ahpv1ShODw/R8d6bGvFTIUI4bGrqV2QcWG4Y0emwMn4O53Oe7tk6d/lKVlnsVGcvebwphw8Lzv/hXe3BijLAeHHD1xwHya"
    "8lREEQy5lYtbbjmHZr+fRTGF+2DgEtWzQrUt2RjKAE9/mkBX7394DRAGsJ5dZPnd7xD4EEdhRoz41PvVoBend79Jy6zAPaYySliYYXTRoryETA"
    "BYRjylSOOA5VDZrmoi9gAtDAvL3Oe7YnNSSIPx/v98INk9MCzzgNFIE9z5+eUUd4JTDIEQkADiDaoCGDQF4PIphWmk4ASyf3g9md79tpDhjAwW"
    "Z6hmwUBVqgV0wAbMwKipA6zICYwgG8DDDcPgDS/ga4Ibb+jEuCTQpRuMLtDij9mM04ZpkpXRLOsRzwXkPjW+Bspy1zjB2BGnpA5Ba+vP//K/cF"
    "Oc027q0clbw7r7Q4wEVIEbmEa00Sd3ZaEzFIkCqECbgBQFYjlFehiiApTP5R4rMACMyzdH3/zCPz01wSx6WZHEPHdOTaQalGpckHSkt0WZTeDt"
    "axglZIAB8jITBEa5B1OAUb1JFIyh3ndq1xFQyUCqgQRlJHoC6yngzYEEg+gtVoaXr7CNIJ95jqbzcJoGJfpBQOPnbMBjq7TnAqWxX25tlTcTNK"
    "CJB77vA7xoSZmHVOCZZi8aWhtjW2oW+A4WjCXaByACRBcb6gSnnXNoX9UMTrvnPfk8XjThOPl4KNT4BwWP0YcIWcl2Ah8W19EFaC2WR2wnRvSg"
    "6OEZcbbZN7cRchcdrsDvmwfZhKCboTMNfZjbiNC2iU/WGEDCr4emIYbnoQlA2dtmH+t1od7BruigDwbwZRalFr62xltbGzRMkSUcx6modLhiRF"
    "4E1tjGMath+nVpPYIY+mBXVOqbLep+lV0jdSuKhdEMp1ZRwCCD7Bp6j0J4BApPjpB4/YPR4/7DNDvYhWrm9nhmmS+EfDkVKxEcfZhiOoB+TyKa"
    "/XGEqQ2VFqnnh2OMInA5UWVOxPTQxsP5mWQzaOGgYgcdEMNSxgupVesZfO8EPtgFsPriL9Lp34ECJyvEsoj8rATivXsH/AR5KCagjRQFg5JkFJ"
    "kva6rJK1gPdStBaDRMRLtpbqW8pPXrE45laUpkuRdDzMUyKuNaoLUWQrQbU3V1nT6o84/AUSQJsTAEleF1J9fGk8l172oUlXwHmgXcS7OrnE0W"
    "P0PsTkYc1ngxdSjV5+Maunl2ZbgB6SVQYHGWez8bDgdPH4e9QZaDYbwjC5+yfdbdWzWmNEOta3u07a+YnjQfj+5+DwZKAa6MmDJqhZWz8BoZQ0"
    "JN7oSc6yNpgH7KrqGjSqe0xiJE7hnomJVycjBjxgNYdmn/B3NpyMzLNZXyBjP5yBkBI4PDdLGSKLVNJ0onlpm4VywqX0Sp6YD9p76ArFBLEKgh"
    "0zZowRr4z/+7bsqiHL0j0VR+EYItkESS/YdHYolTclMYN5jLDmYpXPs8dmmt6RVgZln2QjByQTt0aFA+fupp2hAkg5MhwsACA2UrTM9P2iECDc"
    "LK460t6ApX9IKX+rMboC0ASJlbW7OIX7nodmBRyEsWxaYyIcqOPwSj/Q1MNYvqRaGNdkvZsedovihAbbAteSkQGF30KmTA5ngIF8zpeP+n4IE1"
    "stLv5q/Bc/FoA/ru9ylmqoLJirbba7JpKSKN7si0EItNQXadIpV5TlL5IzuRliLJowattBkdU3pgKlOO0oeNz3BsQqG1FJwLU6mYHfE4VjZOz7"
    "RFZKRV2dE0umMBb6wM8wHsrS363PD9jn1Ij558i+47vcaHfudwRzx5tO93z9hVuhQwkCYvRoDdnIPpwC0Ttfdz0+6BiVAWLliuX7NgZCljCa2k"
    "0i3Km5jLFq9h+sHsu7HMISzaOxj7Ne2FQPGnHaQ3A+Nl6JcYYH5WAjkH0xL6JjN3CDQwSaCHQDmiCHRZgi+Bni8YV/6wp8BZ3Xax0EmFQ134Km"
    "YN613MrQELLaD/xfb2wWOYNetxITgLn7apfx5nYFUAxEfg0sGY4QmiCbVcxOwEEBNQF/0ntqIBTOtVBAApKXY67j7otMk1CGeUUEgrLZH+chru"
    "ue//gBnPBgO3NUUnbMAdA2Z0Tnv5kywA14fJEADMDaGyNIydYgRuxdiv8EH1PEdS/FWIgKP9KDKoGLZAw3oqYkMfTxhrxNDAfWpMru0qGQFgJP"
    "wFdkHiwzpX8N79REj83X+0zs7CbdsYGfgA/9uYlfY3uy6/5mBQ6nJKhEhoPqyRcqdVvynmCblanrmdnO7BgzEyewAnbkSjgKMTmtzHtQ+b6xVx"
    "F1LsHgF1VUaLR9keIq4EqneICXwlmviwZDtGt+vt7wEhqtxf0dUTxafHxKcYXB6MTaD/Q3x4AnyoVo5hVB6V8VGUBzHHFAqg1Jso4dm0tBqvnL"
    "39jq3c4nxBKurj2q59+2Wn2TPBdQULbHYFKjv8GrOZUAOCw5NbJrhTJLkVpWnNDbMAnazSBYnLb07I9M2g9s8CwUuwoUXUbicQo4I2b4EPAm9b"
    "Qvf+FQaffzDxHnUeIh5KY8NyQKAZurlyAu6C0yoCpwbYb1EY4ZGXDKfrjN+Ct8kAXQyYgX0yAoOpwOYhGRolq4ynMr9BZCVtZlExZfFbsH7INl"
    "xZ+pMS8F56AS/BEoT5yO35QrBV7M20+qk7TkB7RYFLi2u/SIBW3jDKi3InAFUdzhN2vXMVheXI+6Lz2UalJnsJyy+idCfmw9Jj0zJbfpVHF6P2"
    "O0oc/vcCC0Yp6gCvCm7DI8KlYt7vf3iThawgdcQmkwL3Zx6TSopihmoKlX9B2p/HFEWt1H8hIiYyLE6Z61X+sDgp1xZXlDYMhxuDLLwx1gqBGz"
    "xu08wgas0rDeuB+ZRMLPCzna77xf7synnqwhe7gf5fONRgaZin7j4MtOc+hnG6j9rD/C3lgVg19x59+SXUmX8iTKEvbbhPhlN3D1B65H6JKLUo"
    "JzOBhU8U8iGDZabwLdvvW/Ms9XCddJIs5J6JEmc6QZYk3t6+M+Fs/GwyiSNeiEqUh7YvnjFxzOtQnV8l3hN33xEJ1F6346h8Za/7yJE5rqLRzJ"
    "Nboc7yfsXqjR88syMl8uTvXjwzrG3M4fju65M38Pzn//rfbUM/5QjVLu7+IIJv44TEVoYZHay16hSPFasDRCr/Z1SdpcP2VmjLBHArtatzPmKT"
    "Qex0iM0KmSj2/gc6IojTbumIIG2JqCOC8ogiJowoq0uksjrYCJQs0AE94psst13jLYuzXOSvoh2DgGuHyr4+MSz09tYfLcOzA/JsWbp8uEzfz6"
    "CzZS+e/cN3/tNeo+xtx5/H3umes+fswP9fOHgQa6f79NxJsPRJu3S0qu6i0edxSwiRht5px3kEvYEYdffBIDl3Ym+eehIEN3aLOArAE3fC5bIF"
    "gKLVTVbUTeq6I73uaEXdqgzXbQX3v+n8wYlB4B0DoNpkEhaiivVjerGVqSBI4CuQLbKFN6Li1eAS3lc7Mr32ZFTp1mSTfmB+NuZS3/3mk6Zmq+"
    "5EbjboxrvfiaXr/Q9rs7Pf/9Gh6bicof3+By1DW8T012doa2cCqsRrbPFLTGsQ06VBbsrVyIipNiUhSWHxJbN6MqZVE19yZ+jn6QXGOrjTcTBz"
    "jHKSpUvfsetNtVvcVDs1wRUyE/g3Ms/tEDONQ198UChk5vcbucR6KnEzk3h7tosjfQ5PQ3ra6dqfU64wfLPtys4PFxJyuROXuVmKkTZ5ts20Qy"
    "zA0l6NdjCFkipPE9F+lufsxo0K+rSCqf3uXTCV2WYHXe1Lv9I/WHjaOUcyvHu3ARVgJuQ3ljVzIph5UYGZq1tbs77fgb8H/l4HPq3Ip+qzPrSN"
    "drrndiXlIcESElg+9CanNpXeS2XJqNvMl7zDNKZD/OvNF/quJxhj1DiFhmHdkPlN5G+zU6gKXcgH7/S8hyykLwgZMtL6nrBE2cD0Oikb4J2BLt"
    "KC7eGiJYcfN+2FWVAdLyJRzKqvTv3GobF7uhhIvdSQhepEi1+9l8dhftIhSPAoxcyv5yJ9dzJKcG8QgF7Ytkh99ztNhwyWxYZyAT2h8hPKu9/g"
    "sq8cNExCwBcjNsAgNmk10FNTgw8poCoVUFvrVO58tTGLh0YDZzpxxomDZ0KzxGFj53YMmt/BU4TztnZuHmJemzHzSQ4xLx/ikEeaSRE29WB9ih"
    "CAhzHxjLIKxPuCP84tbeqf3uLOuTh4fAiTzJPfn7/6+0OYex7MvXNi2S3M/ObsKWkCV0Lc6WFmTgRsxImIz5fwfHkgqql0VjwTDN2Nk74vXuBZ"
    "4Mi/7KkZCqAe3rqhd+umzqw1X5l9iFPQ6yiVKFTP4czrNDbYH+ajDLQilBjD9juOPFHnm6bSlPWE6IM+20jY1haCXR1PnFMdKflbW3xmqz74jD"
    "Yu5tS1dmYwZ1c+/ANNv4OvSNkvtA2MjzrkWMVONSRYeLkGFWT51pb4hBUC8GFRvrV19OzNiUvJVK+gFpDmoGPPG9PwAdH+ZKdk735XH5O9+606"
    "J1vF6ZTwtiU76Xe39eOwqLQOOojpPYyhWrSoz5FiZU+0somKO6XGp+1SMAk7X6im/wEEQ8Ypwa5VBDoUWhbsXBxB2LKehItMX3jKS48iyipUub"
    "45kO3BLjRPFxF9jjqe+31xErVPnZprkyDBnzS3KftR1Le3TeMz05MnYA9pKVvqusrppKOt7951bDnM6kROc3sSyLq292nAknoFjcZVe2b29baP"
    "e8la/2ChUKeiCnaH3NTGNNXeVtVpe5tOdroKSdMR9fudQxPD8jiUvV3RSfS1elAl7Z8UEV0mouTV0J/4fZwuz799cXI6OVdrifza09j8AbXhze"
    "4/ioMC7mmcjM7xMw3xA/c//mbXBZ+mtCbVknUqLLnzeuOtlSQ1uN25oESWgMdxReFlV8ewPrMB/8Ht9zhJTKeAKWGJGWM7piibQ9OJZ3bcfRMX"
    "JQ/GXsikrH4jB4oU2TIgoyjFJKCTuz8k6PdlRn73W+ByzMX+UR6gvrzkGtFlkHrEbmo4O5imCc4eeE53/1JGMZpOM15UnhaegGVVRKTamcK03Y"
    "xCIaIqOnOkoGX6lim38baR/N+USWzZjVXkYRupsVKs9Skr3SZINNAJJDLa3uoXUB3sDh6i59ciRNW4t8pZ1rZK2eLS1NC2jiBbAW44J+LlgkyK"
    "IA8DCX53rbtvaI+h0JIyCvsDsDhq3Z/G8jwaYGwMpAK3LigrjrdXYLrti6IIwkJtrCI3ovAoS8CeKx3jH547xuucJ9E0gXdHGFY3Tjgre83L2+"
    "T1YI7Wb5mFgGVNZdf4yYhOsvE6n/IB0xKna7Pfg9JMDCjS1/klSDpQofuYbPO9PXEZzN0/d519W4APvm7jrjPHyKgX2lE0rEfUsNutGz62XeR+"
    "G4wHx2t07BmrOm5AtOoeL7fl0xS4JB+NeDC2KvdFP4jzcNBXFytx8ZmIoIbiCp3qJrQP8Ga0gZfclTcD0BlavKb0v3KD4YXyVX79q8pM/YrKfp"
    "2Bbu37ncP6KzorTuo3HA7wIfDuILIO0VAetbLIwnInKEjFwwjk7o/J3YdpOy1LgA1dYJxq9O1ss2ooc45vD03swshSWF0Ljqd7WA76FspMkUxJ"
    "mbywMoS335vb4zq/EvRrUfBQ60rUz9IgjoIxZbjFeOyDcLPOzkzR/My0AV7MOwID5tcvwR/CHDMBXyO12bxnPQH4Rpg918jZhMIhFB5j1Jxi5j"
    "LB80D81b+caFz9rPHmKFv3Rn3R8uGUp4heY3SQ9vCsozw4uJTvB9Dl60AGClK46dDsABsOonQyLWvCB0D4iGgrmQkG3IDnyBusiPFi7ArWTFhZ"
    "MbMbFmoogJUavsDkw2d4amaB0xIvXVg8dCl5Rz1qvDuallY5igqHQLDbybU1rRELLZdXHiNqp9UCvmWmC1WZKeT6Yu8CSbHdPUgPeVGBt909t9"
    "H2+x84Asza5UFaFEt/PMXAvMFndg3P+2vIN3PTmnaUYYK9kItqbt9um27qKjialP02JaIukVMXSzDJkKZrcQz/WjiG9+MYfiSO+gRbwvEBpQXi"
    "c71SxRxzMG9XSuhXWZ4zqfNJVcm4bnrgdw9NVN14TKg6bPF//+c//7dKG+lTXY+VjpbtmEGZohp+CIFKw+pzAOD/noXhSsSehaFlE9xp368C2i"
    "sA3zae3f0rCyOJaq1Rlfr8SyELssnNStCO4AXCBipzEgGJ8WCWWEoZbYcIQzAkK/YTwRLy4RIo3/ECLw84M4XnRKvLn//LH6p9ziiNwBKIeaHH"
    "OleweNFa0IUXoK3ogVjR9Qz1lcbxKkOkEWfSDeLiyjL/rlDUI9jAEQP7ErN0woevqHWEEcxT/dZbw0ozeVBNM4jTCMtW2sOZZg/brvAEieAZ7U"
    "CImJvpVOE3+wFrvt6npnRmpp25qc6sNJOCLRVAi4C50wgPYNIWHu1gYy4bXe+aE1Vrd8ozDgb9bSQnbi/KC4uhCBx5VSh25Ndu5kP91bv5rvG8"
    "3ncssEGWTFMAiLX2+kTF2fKuOjbCoz4Az4SYABwmqApGG/mYM71ypx3fpNkMfNhBzuvddjzzs2LDfYWVpM8Zsi4qA1VP528L/Hd8woB/loq0c7"
    "/K0brg5dcxx8evbr4NLSUeImOY2/N66yoKaefKdV2e51lenNsU1cAGp0Eann8vgxhRaNuihisy5rGkx8FITnn+zZsXz/0K5kXOh0Da0THPoxkH"
    "dQiAy9wz3cKsU25v7XltVPu3vQZymDbQag02Tt2Yx2A/r7PjZz4sslaV6+/EmdoFwB1CZxT5aLs0DPhDzYjx5I04N9oGZzb2X9LC7UbFz9V1Ob"
    "gZGWe4GTmK1JZkD1NnAbqNbGz3svFhk3oAExDQk4WwmsiSats0U8cmqaQy/PxZvXNxH7fJTrMAS5t4zmzWSJs1lfEGVttMGGl4oLLJN5S5ZerD"
    "CudrqYGrKU8Rbp2s2mKo4yWDbQCMYkyjFTIpnfnVXjaQ1cHK2/tiX89Kge4M9/SWaOVOpsUI3tu9e7d4W0dX6y1cugE2OBfdyC+nqrCCDmO+TX"
    "ldTTSwd2qiRfdRLcI98QYRwPBZgV4xoV3syOn+WAz1nj4AFTQjHhaAj3ChK5EPMOsiTyzz/Z+kiYL6vw41KovgtvJFtSFubUz/blkyQuMfnp2l"
    "8P9LOh4qL4QU8k+H36dxAV2//+EX9CZ//0fXbMhTTcBsmboAd7aBvnR5mp3789Sje4RTLaWoFDkaKp9I5CKsIPOaEIqMPqLNhBN7koJRlXyP53"
    "r0oKXYWpARYDfnk5jBaLv/eHZWfL7rkMUpsnvQBsGdiMam0qFJmWtCHVTbSqQVHLEFUZUf15sQpgi1SHNHHftZBapVGSKHJluzNSKraHK/bS2X"
    "gS+AXgAt8wCBXO9N8DbXXDKPwcGsib65rcPzYDRUGuw/HdGIw+//9DaLMc7GRKRyjTFcByrxezukSdtUH9iTiLE1yOU0R1jRPYHqXY2iYETH8F"
    "hZmIfmh41YKNtRXtBRmbUwlLRrCf66ezJZPrT7B+L9H68DhJP7UyJbn8fEnP0Ka56YaBChJqU8lZA+eqKElAMU0acsE6IHheJBK6W8m7De9xVv"
    "VBpNqJ4W1TnOf2NAevUCAoX4QW78MmhkzM6Xawua/gzXqq+ya8MVTh7uf4NGvPEGcRaMZaa9h2nTRseAvz15QDsY8kfDfaLGj+ziLK07oJBv1X"
    "4Y8+veBZt4T6GR7OYp9rJotphjRa/bU2fRv8Q66kB5zsJoWtDwPcoGv+J0bOCLTrsb0HHOikTzeyq54JaurzcfsGB8QbmE3s+67ItH/Kl2hqF5"
    "3n2fsc5wqL2uDsfrhQD7YByVO2ie7gyjON5ZWY1eFyPQ5ldeCpZDI2+/AebIaXzNK9Jf5FHYwz8wVgIlJd8RGaKF9xgZCRYmZk92nK7bHea29n"
    "352x6yD9n4GD5ZHF2kO+AKJIUXkJunOPtkmbMjLX+/260l58vh4HHwVB0DGWRlmSVeu62BgVQvBduTzplYj2zn/gqP7TlRjkD06HBJm165CEDO"
    "xYmHbqfzGfDxGgFEuZMshZJeu6NKNlF+HwEmLensKOkUuGINIKI8WdHCrMzuJ8vyFQy9DLTwMAZxGEVhyFMBXlXI4ziaFFGxfsjhvDV11iIoD+"
    "UAq1s9SMrpdMBKLQJf65MGZVcSyuvo5NkHnFVHHR3qXgZYgxPquU+bw197Kqg4r6rs7a88xvK4g8dY7qF4Z+maCwxM9WJQ+DsjQSGYFYuVgqN1"
    "A9NInTnBfZZxillIdD8lGIVWOHDxVHjx7t3puU27X6XflzdDluj92rZDTY4Hfjggc/LH99I8O0XnND39ZEYc8xntmhYgMpnxT9N/MqykoPMbxV"
    "Qcy2RGkHO6PnCX4mOYQgZr/wBD1SFdK4Yr/mWWY6YDWI8cy2npv2TqtqrqgBUeHsFjfQG6OJhGil3lfBbNWHOXcpRNc3DnR9W9PaOtrRHgt0Hn"
    "vQ8lxiOKI5jjd2CeUgW886YEa7Mq4GloL1r9nkQX2DGeF5SujS9uYnVZgT/EZM0XzgjcQXE5QuZOVQbkL09evXTFVUzR8MbKtEN81X1QixWjFV"
    "WYKiFOvgC22T0cv3avRuheIXuxjWAv+lej6i4oWvszgtO0EzwxbFVEcmq09IOFEqhEB4kF5QkSydIJwEBWXHgTzfgJBxpkqUKZbW0xQVVFc/kV"
    "yG6uQZ+2fgEav0ZfyOSzoPTr8XW3D2QiGH+DmFtQUfer0bwZILYlDK4iSCFVXfvi3bv5QouwpNca1ZtO7Sqqz6vkxo3Ru3eK+hsa9dFAiNIp7+"
    "npklHo1/woKuThWy+9JnZFIZRruZNII3GBbmhD9/BuPnKnPhAAYyFFeRqF5+qKDvFtUf26mJi+AMMM77AQgesQf/+M5rGF1wOqy+fe/yDnKl43"
    "WJ1gobvjotyutovaYVGCbsxvgHsoiBuABPgMFAsVwBCg2g+eCZBwllep4+DcyrFhRIwrZ0UkfjGE5CO97q0aWU5GGhvDWzA6DLUjRu1/2fn86Z"
    "PHfL9JmSqO0mosXWdVeZ3EaNLCmiJKvSrp3dpST8AvVsWem5IIKoeHchrd84aElBenqkei50KQEtSkVKgG/YpNXmQGGFYJRjss8uLQi2aY9osQ"
    "1pNLw+M+qBRevNDD4eM28eG1Ij4Cet5/0qI9lfbaZIdm95C9AQhI3qK6ACocAFXl4mXPtVVMrIFABqmVFvJapw9o0NJDvVV6SHVaXQjyF8kR3r"
    "ajLmivx6fpVWtkdQHHJx7BMFCXt5RoPSyyN4u5e8Xy1DKFOUC2gOlwmW6tgSjSutwctyp/RcPgkb/5xxsivZojIsn5E3f6IcxdVOmmMK0qI+XG"
    "uGBAkQivE6JYCR5lEaGfOKPdrZLHd78F2y6jI3h4l53B4ouMLtzD2tpOa+IPbo7Bn7KOxCpiO3FV9FwVjWC5krfj1xPudOzMznHSBQmp2DghFT"
    "u2bagugu+u6wYxpiTN7PbaNcOW0IS2d1BLr2+UTUsBiA91ZKRyhWGoboV9892zF6+MZ/KTUukicDLKaEi/WokHc5/hfiedT2wQSxxWlKSi61SR"
    "WI4xQVtdJCdWJJShq1RshELhhOdYnuqHKOkMdFbdpJqqE8iVEenKfIwXUQGrj7rHlmxStE6pTuFJ5uLtbnKpFGm2ICSYEiRWzSmdbQLvmOF9Zp"
    "k45XQjllRHZCVquNpiL7Wyg8UCd/d7XOHo7CettCl0zuJZpg5zQ4fQN74rcU1E0zqvLpK1FTLHNQHkpaiSFABcxG+RDNcg4yyhXWEm7ii4RSpS"
    "vor4JbQiwRjwhMpwF1YRCI+BwIupuEMDQad73Ij9MEaI/kCmfpRHmknHnIU+msVfo/b2pXlVy2JCmwNHzUXVed78rm/HVKIvtSBePRyBFCe4LI"
    "Io44CwtvjVsc40sVSh7cCX5flQwdBYYRCIRsHHQEHYLoGhShtwSEKBzmoZm9KqCMNvfGvkxFmAeu9BE7PxgyHqYtjavpz4OBIZj2PNotyY2FSO"
    "1uYYfRgVPIRht7Y2EPqJO7X7iAV82q3atBKstJCPdAMZcQFU6OjJaoP6+Yrq9e/jyJqkEZ2C8/RkrX0ODBoRgxBQzTKvRAFPKEhs+rqIqGVUFQ"
    "hKKMN9odO1AMI2XZyWH4nXp5PzVY54bh6amSgtpgO6PtQzB/jHrNlQjLe2CC9S58W4OvUc+aIY+QbFvRbwOW5yI1/Ekz/qtQCmvm3RR0F94MKi"
    "LAcJQLUMKI42VwCxMkAl8XZuVHcG4orlwhJa/VDFPaYh0ZWsw7Kzo4i8ZJtX1H+4P5pUVYdqii1ZnNWbnrHQDgDpXYUImaJJ03jy8Z0QBeU9NI"
    "2r6vDPp+pQGtrLpFvqT7i09HJ1h8JRWfEj06vGEOSsB2k6JeJ1a5imh6AR12xEBkwjSo3nNgpUo9x/3oogLJsZbZ/Gk2lTtPOmmxG0Wg/qozEW"
    "m6Z0H8MUbxF9/0MKs3Sasvd/tPFgHi3BA1oFKcaEMa0BLfZ0YzjD6FMJK9ozNHO0ZW5pWFj9i+gCrzYdRHjDifppCnHiWViBcmi5XagMmB4lTy"
    "n8wP+VYTDDEgGw5pJERw+krSIvhMj05d3AXbzqSBGYH8yW9ztX7jv+fF/u1peGruIRaKfl0iOlRaX1CrYWLOjKAkfdgWb3qDK7lS6sfrVFhswm"
    "PPWZ39/YsOoQESwxcn7KgnMoESOQJmxFkFpdAqw+dmu1BMk+bBV4FlU7aldrFYi7MuUQy+IK3w6FLoQn26t+HEnzA8MBastpKPsQYeHolh8PTq"
    "RrVqlKvCb1eRaw+FUa31j1DZk/oovasXt9fPSo+1hzniw9yrf0M5niZ1RhZBHjSS96ra7rLc/7avUeHlrRCnrJeUDX1L57B46Z5rzqQQgKeRBl"
    "PqbBw2AIKCraoqLE3w3Iw+IrcMMQlTZqRTDi4TTmR8ib17hY2ou1l7yxaTkSv/Vi0gXi9w30MLCfDpTz88X54v8BwgfFHQ=="
)
SHA = "ac18b1e98b527ec7f75f9f8b72b36fe00f82b15403dff8e8230259db95aa9b39"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.57';"
V_NEW = "const APP_VERSION='v3.58';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v358.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.57 que espero (¿has pasado v357.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.58')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 58:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.57 -> v3.58')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.57 (esperaba const APP_VERSION=\'v3.57\'). Pasa v357.py primero y luego este. No toco nada.')
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

print('v3.58:')
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
