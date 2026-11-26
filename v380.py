# -*- coding: utf-8 -*-
"""Super portal del conductor 1.2  (v3.80 · version 1.2)

Sobre la 1.1 (v3.79) esta version anade:
  1) «ELIMINAR CUENTA» BORRA TAMBIEN LA CUENTA DE LA NUBE: despues de las dos preguntas, la app llama a la funcion de tu nube «delete_my_account» (que borra tu cuenta, tus datos, tus contactos y avisos SOS y el codigo de avisos de tu movil) y, si todo va bien, limpia el movil. Si no hay conexion o la nube da error, NO borra nada y lo dice. Sin cuenta en la nube o como visitante, borra solo el movil, como antes. (Lo exige Google Play.)
  2) CONTACTOS SOS EN LOS DOS SENTIDOS: cuando alguien acepta tu invitacion de contacto de confianza, os quedais los dos como contactos del otro (si pide ayuda uno, avisa al otro, y al reves). Lo hace la funcion «sos_respond» de la nube; la app manda tu nombre para que el otro te vea con nombre, y los textos de la pantalla SOS (invitacion, ayuda y Jenny) lo explican.
  3) MAXIMO DE CONTACTOS SOS: de 8 a 100 (tambien cambiado en la nube).
  4) Pantalla SOS: los correos y nombres muy largos se parten en dos lineas en vez de salirse.
  5) Version «Driver 1.2» arriba a la derecha y en Informacion «Version 1.2», compilacion v3.80.
  Nada mas cambia: las cuentas de 42 dias salen identicas a las de la v3.75. Hay que COMPILAR y volver a instalar la APK (la pagina va dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Se pasa sobre la pagina de la v3.75 (el bloque de pegar la recupera solo de GitHub antes de pasarlo).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNrtXV9vG0eS/yptOdGQ6+GIfyWKMmUosi8xYMteyxvcwvI5zZkmNfFwhpk/kmhFr/e4d9jbp33Zy2OwyMMhONxh92EB65vsF7j9CPer6p7hkKIUxY7X2MBG"
    "RA5nuquqq6urqquqJ6crQz9QyUrv2enKRKaHK72V4+PjNT/01IlzmI6DFXsllGOF+4/lyA+lqBypOPGjUDScZk8MojiWsXAzFaZSpHI88FUo8F8gRZgNlC3c"
    "CE/cNErE/qN9foJLD38Juvi4sMWhTNC5Ua9XgU15fkr0PFtxJnI6RqNaNEkJIf2u+YB3OgTMWuK/Ur12c3KyFfihqh0qf3SY9hpngPGGPQ/CtV+Io5azsS5e"
    "/4/YmUzEVHgyPf8GvSLxi7WDUANKAhl6IhnLIBCOK2OPYJ8e+1562Gs47Y4ab+UwcQl+pb4rg5oM/FHYqzmNJu6OZQx29upifXIi6qJ+dtPQ/DDyZCAWRsBY"
    "TsFsT8U1NwqiuHdTDdv4t75+tth2EiWno9j3qGE2DnuNtVpja+yH+UA32hj5MFAnNc+PlUt9enF0vDWSk16Dns3jaQ26zeE64SmGmo/OaWMketxNp95ZNtjW"
    "Ou56fjIJ5LTnh8zwQRC5L88uTNICJ9dpggwmmqyzS2e11HUBfxpNzlae289Wbg+yNEVLN5BJ0j9YWQBF/Q9WRBS6ge++xHNAHfrx+LFuVrGogVU9WNm+nUzk"
    "HBimAA/+9offfn97jZ7qNttPZfylSmV+b01TgAvPP9qGkL57km4nR6Pifs4i4fo1OZkA9JGvjj+JTvAM8ifabdGq466MfVk79D1PhXiSxpkiSCQngpo20GRq"
    "vnmecN1u4oeeKfxqdvErprYdXEC9BLi8qerNenN4sLK2BNbGpbDKENZVfdiQ8xDWc2q6JRCNehnERk5Nw1kvQRsOB63BArRmTlCzXga3Pjc6hmIAtuYAenWv"
    "zQDXwPftOVmALrkgB1dPPxbxlbOP52byL5ljDeDvOseN9Y26Wn+bOa5LqJrBTzXHctNrDLXMkW0THm4+bHacelM0Np1Oa6flNAX9EW8aQj9ptpz2xgxIGIVg"
    "jkjSOHqp9DzTv+JWraDI2ZzdJDXnyglux1EWeoskbDjNlmhsON3GzroDE+DUcxL4CQhpbL5jEjadNkgA5u5O1+kK+jMk8JPmurPZfLcktDBZbdFow0TsNHAt"
    "+EMToZ81u/h8F0ToBcrr8W5h329rg56k04Cg5zaLjdUW+w3Hxn7W61szP6JBZiqaSNdPpz1nA9K8nWrNL4bn3yUwRuRMGAfJjcaRSAvDQAi3LzEQZLVmyz+R"
    "R+pXAxXvyuTwaexPKrT2P82w3uF9HfnyS7XQv/wJY/M2kK6jqHKuabemBrurGWOconr947IH0oHTszWRnueHIzwkd2TGz87kZE7z5QQ/jpKC3g9a74PW+6D1"
    "3lzrPYiw6RITOZJeRDu02TZnuTYq6aRhFrraQZ33SIxaqJ76w8qNiQppbdN6rcYqzeJwC82TVEz6pUdbaGq69ft9OLTJobW6Cm317nCw23RKKuXxrI3xpe2J"
    "I8fgVmqTbqhuaaBny4mcY8UiPNPepsY7bprJoHpaHtYFlXbZgC4jdHZrjmTsYH8ETTaYAbrY0MT+qFfAClWKH/i0TaezLTIhP9SGGAWIKVGFi35ja55LEch+"
    "XNrkXj5sYDtGCCI6dnYeP77ftz5sZN7jRsbaMnPx+NH+VXPxwfR+ML0fTO8VptfaKqnnH6EMSYl+dJo6i1bojoWY039bvYUnMBD85HurZ1kUDf2RfSspae87"
    "pUXfKynjKgPlkJrZABzJIFNGFxysWLcqy+hBtDfA+lIeEVW9ZXG4TBQhMg1q26Kw2PXBrq7e0LReBE/BW5i8UYT9SUzBaDnBdgKbtPPvw2qBbxEXq7BLUF2G"
    "abaBrCzs+6qlcRHDtCNRTMHXXxe/KJA3w4lvsoBXNi9+aYdmrnN++45u2iN4M2DcITUGWgWJEh5GlCrB9/TUWmYkthpSfPgosomVthsNYnuM+2BlxI4E3Zeh"
    "ZVs7gZhkQSKZ19g3p3IYxWNkBJSYxGqU8eb3/HvsftHj/HuhAtgQpApS5Yh9XwwzRamBAh1mLaQ2+Q0RKwTFv0IrogHpAnQDi34knbbHdIXRv7TswuHFdTo5"
    "wqdJVCAbkvxL662G1BP3ioHkgogGnko8tSiLIhJXSNAbM8d0I+EvRmovi0IgxRFG+k4OD6wlIbiHCLoqms0eAwrSHxHxIYhyVigH06F7qLmxR6UMyoXhXQaK"
    "0N8fg/iUpFOQq9wTtwfCJz2emeDFI/ijSEgF8CSAe9Y80FGMqzsQhgTo/Pj8G5ElTAV6+gZKZJrm2Gl012tusOsxaA0uTof2QCbKdm1akPbInrhw2BObhMpO"
    "/UkC2RuPe/ThJ5Rb22Efu0KdqjayYw9lCH+ddLnZ4WDfkPTTxIGhSlVcSfvbl6qsKrn5T+Rxnzs5sfIyV1Uq0k6r/W15q7KXjQcEgnz56tdf16u3HsJiOmN5"
    "UqnbxUNQyQ/tOsPrl9roSz+saDw8xiq3+jSO4CX+EF5i3rUQw3wKsZylwFEgpIu9nsYaqHCUHr4Fx2kWoR1FGkGb9Ou2S3/AiK8R/mivk9C3/qLu+CIs/Vcq"
    "jh7jolJFh5D6Se/Lfp00+yUAia/8+an+2nsLJEQ33bnVP3Ewyskd/eXQPRWgB8ac9OpbaL7YBLcy5GMHgeoxtT8FGIyGnuMLc0m/PjU/ecbMvT1zb49+z60f"
    "wIlTG66RzWxjld4rVhPzR88qywRPMgi/Tu+y4JDMfMqMvxTo3H52AC8Rvtou4FRSH4bDPpnf5hOGfej69DMk0it4qFcvT7cR8BNOXZKEX7qsipa0mKlh0YhH"
    "UK9isWEf3Oe9GNqYuIX44jZiNsVODeYw9l1Ryl9PzPZ5Wwe+tz86Lbl5ZzpjpQPUAzxTWRxV0L56htBQHhX6QQTsUF1AQD7l2d1SxGkBDQ20hOaLclhjOdPZ"
    "H71IzQz34ziaQEMnM2RFyNqkuRtdd7OLfRiIGMPvn4LhNPuke0q0kIP698Dz0emi8JzNC1+syPRAnQ6qp3P6hML6RqfQd1ker9uHdKfRROZ7j0FppYI2vNZx"
    "odVD+QZ1XVjpT5ct9acX1vrtNN6+nXrbT4moWY4Ed3B3xm9iGTOPJYWRE9+o2Rog0Pz8JIAKKMZlIU+K18Q14JDY/yCwUsT1apCLwD46ZQZu1+98kcPdJb/P"
    "RHLhgZQ8LrhV5BiS+xtHuvbGOKlJ9RqIP53D/EXvYOVgRQsi1Qah+sebOgG5HnA6g14YpZWbr2TVXAzyCze/8PILVRU3yd8GIcIxSxrJIemJW8JJsjHSSNMa"
    "1bCIbeHoNdYL08Oae+gHXqVb7fXkEI7P6UC6L0e8ze5lcVBB1g5ues8fy5GiLfetk3Fgf9zapZAVLsOkbx2m6aS3toYiJ+e4Bd9jtNas1+vU2CpiVxbFBJoI"
    "B7QtHQqwKBJg5YEA6+NmC2EAaz4KYDWdprUYA7CYtrnbX0Z+mN//uHUP1Ll+7AZw3oG4ARDuVH/HfavrdKw13ciEMayHjabYcDqfN5oBgib5U6IfVwcrVdGp"
    "f0x/a50uvvEXRjWsewXrBRHxURkzom+KpsOAQ/EoIVPuVP/YjkcDWWl2Onb+52xUL96sV8VG82ONCTm+tQ18t+tlTDROGc8wNdbrnhrZNz3Paw037Juys9n2"
    "ulVyaD/I0Qc5ems5Ogjfpxht/LzEqCwhLacTIFEgOk4bf5tOt4boqWg7DYRMO073AZogpNsNah0EtZsI6TZwxY1q1Ahdak731T+YdLnewB0O7Ztdua5U/X1L"
    "189MSZksiwVsU/40ABt1K0+vWI11i7IrVmOJ2lp3OmLzsPOw0cZXE8LZgdx1jtYlGgv605mNlqh/DvHsis4/mPAhndeWdfum6qyvt4fvW/g2f9aqLVlHJgx/"
    "KD13OpIuOBlUw9O6W6+1nE2xXqNn5uvVP5wsec0ByZLbdTud9y1LjfoHd+uDu/WGclQ6eJELUV6gSZN8Q0fiJcpQ3i9x+lTIqaltrMVc7lgvkceb5wmECUOo"
    "qSNgSXo6z7yNkyeNzqGg9GIUF+Gm5W3vxj6OOtAZHN3wILzNcSad8Ujiu37i7iYUfDsIb+qfFDbw+bDH0D9R3laghiBty5C4RSWbdRz9QNXXGBevanwGiEo3"
    "6/XGVmnFsmC17EbdbrZtp9usFsc76EzJFh+8qPmpGid8o4bA6xaFgv3htGYY23MpAhHrqs+hHPvBtJdMMVHjWubbFJYMVE3fsJFsSWqJiv3hWTEUTIRXG0Qn"
    "p3OYF4606NMvcxWo8kSv+l6nSUWn9NtUpG62jw7Lg7xZHzRkq7WVn7WRw+ZwaA7G9Bo4spNEAUTAHI7JT8wU3DO/aSFlSa+J5Sb4AxoKz06o0pVKX4tuJwtj"
    "I3k7LQpk6YhQo4uPtqmU7XXrsFObWMQQgI4oWHeBQ960gFLXILpUrQzRGQbRcW3ak1kabaGwefDSR0Vvfj9x44gFHwdoMvdQ4+wQzrbTYaztq7GKyak54EQ4"
    "68taZMFck7wcuMZiSdOzrFPgXwk3DZPriAQddOouVCBr7uDkkFuhM1BY7Co8qiRyqGoS+VWshkSlZoJttK9W80nmWueZRDRUS64PllAmdEWlOcV1QUj45FVB"
    "UYvEc1Yw3e7OzTwJRMH+LTeLEwipURTLMN9MvF+rpGx2bzY76y01yOUbdvGSfnvRXLfGenOzLfNu7qa3OeygJ8LdpH1YDbnInKRlPYSgYxYrVkV0vq6BjSEd"
    "rzvyk4hy4ki6U+ySUqda9VHSFTWoiN4GEplsJY6U2Nl7em+fHgSBOkJKHpHdLEHRuh8JKXZcVyU+dLXvSc/BTzXhjLXnu0q8/uNeJGDSXF8mr//M8EZc7c45"
    "dfBQjKMjP3D4fJ9JUOw/eXH3/v5u/xQZxwBLsWc9lrHEJVQuyESi2vWJYpGFOt1rC6OQP8sGorVeF/AjQBKooOYqHuuxzlPKN0IvjnwimkKyPHLlnX+HpHKA"
    "BDrIQ545ESaKeyhd1bNsEKXV6zNKiD6zfpmdf0u0oWYB2FJ1kurmCXNOn8XM+UkYPomC1Oa0NpL/u3IAxSzGZPBRO4C2CSW4k145v12ktW2R+ASX4skcbS6V"
    "B8wqFMSU20n6AXBPqOigNGaGhGOfRI2P6Q8xNaCEaPcVMApdJRENcZZPOtZzWw9zVo/x+o95tp/U1/j8Gxz5i17/GeMfZIkry5TTqJQo2MKQE0GmVCJLw2wC"
    "0hA8loTziOjRgkFyQfl0BNERSB/7sVzkox/6JAahr+Ejiu5F1Rm9u3KCPJxM8hoCkMc8VwkYh3tJlpgxJiTORvZDqjEJbCGT8++YPK4XmfDcQ9zAdQ3WMOlV"
    "FMo5foGRAUsqwTQjsNECfNBrbHz+PYv7gxkojC8pVkXIEwzld/5difksY0RHzi2c8wU2jAlqjxMPkUtDAqzxIIacTGjBKCjN8/+SNBEgapDFg+xLKc7/BMZJ"
    "ooylsySOkRHHGV5ed18BOTDF8HxVqOtxSFFnxPCYRiwxb9IUiyQ8HSxjVNaCgroEWmRPYmiQlGRhSGHEnAV0XLF4wXOElsYQQ5Jg1iRaYDlrk/rgnF5exGPi"
    "nAxUibG6noaXHk2y5ibRQfQ54h4naExTZt2M8wGxJkixDcrnMlDn33nSMJPzOJnyIC6x4gGzevRN96SkjDAP+QJIyuouzeZKgEBJzCoGhKaQRj1OcAgMYi4N"
    "oyiF7gNSmnJOIgVF/c9XGUQAaAF3h/w7Vl/F2P76r79d0HZ0Z15LOtZBeLZVaN2ytejnSUvURR6EedVHqI4FMqzQpqpSNMAQouBIcTuRxlOqo8SZLRnsYz1h"
    "R+mMVHof+hJnJj33RRK/8AosL44aVrV6aiBU5sr+z1yZuocVwD3LAZPhiQKv70VuRuJLkO8Fii4/md73KpYegVWlcjs0rOIPhS+wL6pSXYBHsO725+2NHc1A"
    "u3A6UmWgVyz4+AAbOTCrORYuh8GdMFTxZ08fPkBpdjkzrT1kqlOOzHk2GUSjvBZ7TDWnRSm2vhfIAa0wbzDl7k8pq70AkfxSNNfGnVv87Q+/+414cMFui8rc"
    "5FeXFAwYn46wTLatW3cdsrS3rNtrk+3bWcB32Myh1GEym22fpouFwbod+FQ0YN3yn9Wf37J6lD0X9KvxnMDgqXVWdWjjXuFSzdtrAGtwkWQbXMspg/tDlJmz"
    "b+l0QjzUv2YMgFOFRuxvwOjxqw581A3FFw75XtJ/L0L3mXuy9NCNnucih+9BN1WOUPEJeYyWCVcuzEfVMy0g0BvxdF9p+1KxtC9oVZ38hF1ppRHQuaWTXLl0"
    "bFqPqOMAAU4a3cf7HbAbDkeVapkeJlifTtm6jKC9aDk93HcoUaRqOhfLg7f3sEdQsrscXYp0eZhmy2VDHqJ7srgUz6gngYcTy77r9sVyEj8cRjXz4gsWi+15"
    "TcaFG4N4+3NqgrJOkRd6TnqQSBTUvPj83pP9+4/2SOaW1ZFcF8HFepINKWlrWjpA2aYDlDNSNP4n9x7c29m/R/g1pF3YJD/QVaiX0MilwE+1wcf+BwtbajN1"
    "NA+76MdexRFa84tAzr8NoVhifyDZMKSRRy5tKO6HXEjLmB0q+b4OjoJ+UXGvoLx6KQkMFPst5R6yt3mBDh7tZ1EAe5tEvJhRsWjU2oJ3X7mIlcdxzd6XDc0W"
    "y+ASXYL/waqYA3GVyzYkETvxkLsEfs2UfQbthsegr4BSkcfST8USu4u1iwJSveTM+QNaVm+P3RTA30hSBz4cqgK96ik8J5QjaWBwxwP/FTt3M7eYnV4QA4dl"
    "NopFKPT7ygGRHrnEYMePQjDZPVTuS+XpYW9pUDHa7MtFp+BNKKaRG8II6CPoLNjGvkymoVtBLSwPYP/JScGPfXILKYwRhT6GyNuRwm+3ClpI1Wla0dmh8yT7"
    "KoX9GZGGm52g+0lx/jCvjdBcTRyx5EkFR1B+9+/wvB9jeWAVko/I79vBAQVbe+cz53XKmwC41g72vyvJYXRMq/cutp5+AOtUQKB3YtBbhN4h9Fsa9m8A5qLf"
    "k8PG2ijcdvycmpMCuQ+9FI82V3oEZrmw30CHNkokGPeHLAZeyaQqeknkLXMgi62sazpqlv3MeKPsjz1HMW8Ic1nJb85cMr+/bRwv43RVq3njAgS5Wc+rtrX4"
    "DgHJFr703oBZlHbu7H9JePnc/84g9uMLUZRcUAv/ySKTfl32EavJByu2v3rvK8J8y8jGXO/5yLBgaZSiU8vDHJiTNwZpjCHV8dERlkBvH1GvGS0aLd5SPVgW"
    "M7uEKhoq64CZP8m671cTLAy1FyGOonjDBfqv1U4YJkdDUbJkxHJEC9UQ+SQ6qmRawC48gU+GaurdyFM30CiHjhNMRp28eJGFT+NpvzL/m48HNGhbNX//drcK"
    "F/WpP1ZRllYu0GjjVR2F7oIJQ/gRURE4BIg5QXHTbpoiihIxZUqo5SE4EzxDk5EOwBjHrMf7+kzBvYY74XMqA2AocKittK7v3v3Vkyf39p7mZpzqGJrsxS99"
    "/GL30d17/Va7TcW0l0Ao8fYH4MzzuFLqWF04ja1PfWEp0cGHz1utYj5vFFb+9V9+SXt8FkYf0WiMtYgg3Dk4CPHfvYQtnRbHvBXOyFCIRkcapvqFb6R4EdSK"
    "sM/BO99gUqpi5l/MYf3r7//z//7338T57x88vf9wR+w+2vun+08e7uzeP/+PPY30QQEc86HfQAeUrG0TiiAi4jel2OmMMh2S0fONWAZZ6dgRr/8C8mk1mgVm"
    "YlJ00CeO7syTOJYv1QPaGn2CaHiGI/tby1bJu2XqLHwzZW864agNs9ae+bvMbpW/gA/epgm3Igw95PgURcv06/iqP495EIVSwDZ1N4gy7y7PQ+7R6ZHhVM8T"
    "HJTj5/BUOFxEVfCJSvphFgTss+ilNepr3wXg9rOJpAMgDkLNh+Q/7is+MATE1HG0ujpyqHoh/8aWmZ8vhHuAHw9WV/HhZMhmavSMX8WL6OMl6OOJiygQD+vF"
    "ePpCahGDoUP3Sry6GjsqjqMYB0QI2Aw7HitoYDixTAcRQtiN2wcjdUinBD28iDF/l+NMyspSlPisd9QJzyNMEWFj24vRHKF7jM3KHk/vodSgAJIMngOblUIw"
    "YZt4kxBm6kiXqhfwSh4mE3npfNI49IaEuQVFF+fKP2+6jwVJ9+LFiJuY+aQX5jVBzvoRgJwiNj9BjoWDIIgeLYDgcIFR9rA7O+i6n0oswoq1q1lmVqunE1cI"
    "4uHcJ0ftcSwEOyYCy0FqEm32Xgqjk69z2G9wg88blhFcxpI7FzCXVUF5Dt+Kot5PPkDi4UWRT8c4Q6GFHTrqBdQkdiR448np5IXv9Xwc2CLRR7ytd+PGVCVn"
    "VRsJ0cLGC7MK7uDzKRI+lXxV0KH1YipN27yN4t0Sh77UGxOCn/Sa1N54uocv7HFywrDeDBGrq2uPP32y/xSvD/l6N8oCD9owRaESikZSLMLchqz5DhgGh1vH"
    "0kxneNYe1jHHMeFuLzwcQ+fAl+Xn2IK9X16yJ8TJgdyTghuKjET+IliSBTYyMnwle5Svmfi4JacZy66ijErKlgQJDbZVc7tR1hwAlw3yM9R0OPfaCI1zTHkd"
    "2ETySYDh/Bs/yd9L+1NQZMPuGSiJBiPS8z8h41kChWTPt7or1meaTaU+MrxLW4QMdpITbTweBAM1wTFHuKGf/fAIuWU9eMFb9yPO7iS5baex6OgL9WMOvQHg"
    "nFHzfEIvwyrq1VscqB4j51w1q3ighiOUQSXW0tBT01ByUu1aoyAGjZNRxbo/o5P2VvApIUmzgZlRBZz0wszAK3Y4VZnUopdNiwIEbwqGuEKR3XnGYEa/nYnQ"
    "PC5+v9LL/rwDSPsGLj4oC2kQFUMv3loxucPkvg0A7aztm2TjVxmXJSSck/Uinj/yJFWIHepsDDZNYERJYz2LsJB5NC8yL2zmJCjnAdNSvNUxQ9ZBQ63dVa6S"
    "jA6qQPlI2iWCvNqUQvNbxi+hacH3nDeAf3g9cbJrYASR9J7gNzywicQm7BN6QaP2A/M45Rzs1dV/diZZAiMPS8rbTtpw8vzvHFL+WG+Vy8wrKkP0+maPloKc"
    "Ax+xm/np3SriqnqoWEH9SoXphVNGX8jQuXDLnj1H/gHKvnLS3z6hPF6/73szqt8Do9jcqSPjJJMBpF83blQwhtVVfDjRMXKLL9QY4SkzmNXVHXh2U8dP+FsP"
    "1IH/Vc1Hi2snQd2BHqeRTg0DAzGGawE4pY8eRMf8mgYYz9XVE56sLOGhs41CIKF6waNbOtsYhJldXqMk4pLneYmy5zKVYERqcabyHbwBZonI4N0vO1pS5rZa"
    "1xQZeltMWWxy+vkNLBcH8dZToN98sN2nt6rPccMRv5Z5FQcezt7PXqo5ATsC3hlIVG/w3kAvD5gpMpBahRDTdKHPV2ZDy9U0ijmi1XrBKZvWxfl3tAWYXz0/"
    "wIZ3u3L1W06o4IMMwOs/orRgIOPXf87rVuYKfmgDxDYi1rsai1948oadxa6uocjCmf42xSbzVvhqF2Xe5upqs5LRNdNTMrozb0abXZ1dQh2sP45edHvWTDS6"
    "pRf3GyeFrSiZTt0cwlPuMCdL811MMPtJSTARuDu81deh67n7JK/0hPo8PP+GMJVpcYr0af5wDq+zLJuPCYd/WmTdowTnuO/RjfJrLR1qxo4cJq30vwlotKji"
    "dfaC3y7//wWu3bhoObDnOuGXrNFhcX5gLukiSU+LMtzjGIWqMpweH2J5wbF+fvb87P8BtNAUWQ=="
)
SHA = "d680c3e6fc1e238e3887dfe64ab8f1eee141b3b2552e795901c3e3fab04656cc"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.75';"
V_NEW = "const APP_VERSION='v3.80';const APP_RELEASE='1.2';function appReleaseCode(r){var m=String(r).match(/^(\\d+)\\.(\\d+)/);return m?(+m[1])*1000+(+m[2])*10:0}try{var _sv=document.getElementById('srVer');if(_sv)_sv.textContent='Driver '+APP_RELEASE}catch(e){}"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v380.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.75 que espero (¿has pasado v375.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.80 (version 1.2)')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.75 -> v3.80 (version 1.2)')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.75 (esperaba const APP_VERSION=\'v3.75\'). Pasa v375.py primero y luego este. No toco nada.')
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

print('v3.80 (version 1.2):')
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
