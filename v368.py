# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.68)

Cambios pedidos por Juan (24-11):
  1) Aspecto «relieve» en TODAS las paginas (Calculadora, Control, Facturacion, Informe, resumenes, Tasa de finalizacion, Ajustes, menu lateral, Eventos Madrid hoy, ayudas y avisos), en tema claro y oscuro, con los mismos colores pastel y brillos de ahora: esquinas entre cuadradas y redondas, luz arriba y sombra abajo. Los circulos llevan el anillo dentro y nada se pisa. «Modo ligero» lleva un relieve barato (sin desenfoque), para no frenar el movil.
  2) Menu lateral: el boton SOS ya no tapa «MI CUENTA».
  3) Control horario: «Metas y horarios prioritarios» se parte en tres lengüetas, por este orden: «Metas y horarios prioritarios» (metas de semana y mes), «Plan de días libres» (días libres, límites y plan para cumplir) y, la última, «Horario prioritario de día» (día a día).
  4) Últimos viajes: la hora de «Aceptado» es la del ✓ de ESE viaje de la lista de aceptados. Los cancelados (sin penalización, cancelé yo, canceló el pasajero) y los «me equivoqué con el ✓» no la prestan: se coge el último aceptado que sigue en la lista. Los viajes añadidos a mano o por albarán no cuentan, y si ya aceptaste el siguiente, cada viaje se queda con su hora (por el importe).

  Cambia SOLO www/index.html (Java, manifiesto y nube sin cambios; hay que COMPILAR porque la pagina va dentro de la APK).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v367.py (la v3.67). Hay que volver a compilar la APK.
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNrtPV2T28hxfwW3vojAmYQAEORyueKqbN3Zd05057IU50FS+YbAkMQJBCAA3F3eal/z6qq4UslDqlJ+dF35weWHpOw8af+J/0DyE9IDgCRIgi"
    "S+Bhiu1mftgtzB9Md09/T0TPfcnIwME3snfe7VzYmD/Ak8nVxdXT02LB1fixN/ap40uRMLTTH5y6+waeBLzM057L2bGRbyOBfrNrRFOjz/mPNd"
    "7HEmtsZ3/4N9+AZb3DPb8l3b5Ca2i1zD5vhV1wLpG+uGHyDw6mRo63Px0vB81PKwxonIcThxAn1jV5zobmuILAu7zY1mP9IAArb8G8f2DN+wrb"
    "6LTeQbl/gTY+rYro8s//z7VgC2L9++tp489vy5iS8I9IpBwlPwwBn64PWJo2stN2Tp6xP42+PPuMu22O1xH/6Lc/ezmh9jwAvp9jmnmci1oZ3t"
    "aTMXPk8BuAF/5Uzb4zTbtMmYzLmha5jkGx1znoGnjosFkXtu6zZnGmPs2v0lyA8/6NDRh79COwuae9ga2e9mmOOHyEW+Da999vi1RQaQC/hi+n"
    "3L9vkffY+E6GG4eNCEJa+44cz3bUt0gFEj252KQ9v0b4a2C6xuASXGzOsDKVOHl1XnuqkhU+PlU7F9ecW1OFUW28610GxL8HPF49sS0JgNscsA"
    "GhoaGqM5A4g4rnGJfFwfJshwSSf1skIRRy7Gln1VNxqOoYMlvTbqw0NDlobN1tC36sRhCtaupSHHn7mbsqn0nOtiUHTjUnS8JIukqCX1nWBmSu"
    "s70XaU1nuyQSit+2Q9Kw/7ZP0p3r/nIEv0XcNpIY24AN7Fwn4FHzfgye0y6NF8E5yK/YBKUYbRDPQM3B1Dg0dQfqAVm5ThgmNF+hUpwrLQpWhh"
    "22rBwwICPIJpCwBdbgm5nBNQmr6VMvouq9PkUdjondjz4rI1xaA1mujbPjKfB8+bRHQPgVm54kJGsFlAraBQBJK6ax0Z5rw1tX1ijbd1ohyDCU"
    "Ll2lcimc5bOpoTPSldwggcPBoZGixStDnM6a5esmroLrqC3gwfT8vi0nrPGiykNvVZ7hRlTATDt8djc8taSCX1Pk7y5JRSFNsbL2yqTQeAAxMR"
    "LGKXM230eRucLJenDOXPr+CPGKYXTObwTIVTifM3HbfZbJFlIxVrBLIKs8TmAHRL0oTd0qOWC6H07teUjY6mYdew9ZaPhmtubXkO0rpbCyvMlj"
    "ejI0Sa14Llq0mFTVHfwW+ggTaMwGWqaLypDDQdp3LNZYWfc9c2k01eOQ7sAsLIsLaHoyzrFC58RG3qtEazbfEtxQsjncdV3LaogqHW+QS7NhWf"
    "m3SuTQyHGubE+Q0enKRB7pUJpvTOF6E56B85TvA7KcjVpQBnR0iKBqjk2BoNSEnRxy4FNU8tzOFS2/SFdAvhg8GVvuVPiDqZOt8RsmORZeWfBR"
    "dZYIEjChNYtJnAQq0Bi5oFomZJqFkECo59OZah4BCUjkSbBSSYGI5OvSKZe7LKtnBZxWxSr1pSgSsQFM1GTgTIw75vWGOvZTsBdS54avCY2rUp"
    "Bahne5XDRJpmz6yqgTrO4qtqAfsTPMXb8VHKUF34W+kDWyS4n40q4o5HYtIaIn2MU0eXc3IPvtCRO6cLRkfWeGvhVzKMjBvBBQxxudZ3PWgLo2"
    "6+pWR+84emssPxpy0TpqqLXbZhSp4S4kmUTVIAtg6YpZNKmOzmjs5lAaGj+RIE+QhwxIk9T73rkgVWUhyqlI6xnjosnmVGoM0P6Hw0KrfnFebb"
    "e/eyUkbXQ1+cpt7SytixQ6tjTKVj4PKQimAUCteltuKGNdpvYXbvo+cDBn/BwcMVcmnN5QtYSbZGKp8cylQk7JvIKjUJoDz8BJLoOS1vNqxM5G"
    "IwK+DjOnWUSItYR2BmOcqTnaoJNjNuruVzqWZDB41xK2ExWa6xs1umPaZFzOJYTzXU5IFyYM+omMuZrvNMDmC6I3kZPZ10nWbycVJ36ZTcZSb3"
    "I/PoU5JeymlgxZApORmsGDKlp4QVQ6f8xLB8gaDS08Nys4VGklgBZCikiuXChkrCWE5McqWN5Yi7ZUweywUhUwpZLggZE8lywciaTpYLSNaksn"
    "yUZE0tyw6lQK5Mru3YIsksGbdeSwFFP3smO6giOTTZoeXNpMllTzOmpuSCkTFBJcfSKU+aSg4DUTxZJd8CNGteSXbSimWX5GJlphyT7BAyZprk"
    "dNIy55sUgUMx2pU99yTHmBfOQMkOM3MeSg4QGbNRckPInJNSCFK2zJQypIGiGNA8BVBGrkqB8xPZ80lyiMWU7r51sdySfCAoBsFz5ZnkBJEv2y"
    "Q/MEogimaeFIaWNf+kMMCMWSiF4WXKRSlsIrKJPQsBZhbiymyEkxmJItcbPGYhZsxEqLj2CHEFgWFq8WBqYWCK0V+aQV+asV6qIV4aRaHKrwhF"
    "+2R0FfFtWrFl+iHlSiLJ1APIlFKOaOVpUAxzU4xuU6hVRD+gXFEcmVr4mFbUmHKwmGaMmF4IlVrklHrAlH6clFLEsrJAJeW0pSrCn/QCkfTij/"
    "TCjlVEG+kFGSuJLVYVUqwoklhJALGaZPkqc9grTF2vMmO96kT1SvPTq0xLp5wsTjdHnGJqOK1M6gqziqtNJi476bbcXFtKKbalZ9aWn1Bbdh5t"
    "2emzZWfNlp0sW0FaKb1sUnpJpPRyR6knVdJMbaSY0Ug7kZFi/iL1tMWashWTthG08Kq51sZHWFptQO1If0cbqLU1iVcANCm8VAHYsYvmojZOCI"
    "ZWBLw+khPWuRVCt/2J6CMnLQK580+KK1bZoDOoV9mgMylZ2cBzqBoNFOomP4va0cIhvfKFGJDbPk3Dx0JZt2b2pdhto0P7uuVNkG5f9Q0L1pWc"
    "xIFjwIEnybnjIeKVTqe5+Ce2e0Jz0apFmsjSop3UJP+Jiiw0g8+q2uTkXqfJnZ41OUlUBU6KuiXuGPnQXAHgVj8ksdMJ28phs+BfAJQqf2LB2k"
    "r4o/SAYGBNWyU0tzvp+dOuhT9r8d9KOCSrMkiPBHRLgQjBq+llqA4WrYfiq+ERsEduK0u6WVWz9fOTdRgglqVn82xnNQZIBgYRHsky+/zZOE9X"
    "DYNU0Cu5S6Qno2p1K+TP1pHYanhDbE6HCJDKsvAkHtetxvq0QXbIvKWogfS0Q6pJ3yR4ySWFpIoQvH14+MHLSzz6/ODc7Ti4/eDT7Tx3/uDK7T"
    "w2/+Cq7Dz0/+CkpL3s/BCn2oBbJ5FTaoxRpMXpBp/kXo3z8Z5b1+8pxemvf6+CAcSgysFcEzBAOg05oBIO9Chw4PBF9Pdn2A9ey3VTlWetbhNY"
    "x2TwwIM92V9bXFAI6AQenHViPGivGgGZMmixfEZEXdml4Ger2a8tUTJxiZlnW/Sp0WgcoLATF4Y1Gts7vEIlNsErsZFeH+gyxrhQ5Td6DNlYcV"
    "bCjyKF6Shyour5bUfy4j2jMDl58p4RuZ28efwEJiaPJpJ1mkiWHKOKEH62MfvC/EwjRrmWNHoP1wWbCazl0lS6ZiRUeaxiUDY2q9QKFmvL1N9E"
    "gtTDqr9mIdJ5aNRt21bqcUWuZxVGe1faMz3T3QbizgipvYBKOR5eUmntYiyzrsseuvJRPVBrsgLDQQaHxNQX2wftyJxLNAUxlqx9z/yiVbL4/S"
    "Qslqx+fwlcHLS8ZxTes2DK/kIB9yhitFmkoNwlSYwwRV2Fibqnq3lgERihcrArsT7CvT1isbNGbVVTvbTaH44PMXWCKZlTKvhGeVr0zP/GSCjb"
    "qrYr+i4v/DP6G9KxIh1HM3JbpT+YXwLEiokwjevu8iTsR8iSy50wL9T7iqgcI/LR2cLaUM94T9DBHeq+5U+IhTR1viNQ2qrl5U4PJouzU5gB2s"
    "r2fN3kNNu0Xd6DtuRMjnzWlXrwcHqqdNQzeDiTznqSyj2OHQ0M3lczzx257nXKwkSZGhMVsv+ptGNbeXt4KPW6yqnagace/JI5uVTmlS97CjW2"
    "EQ9F7ZD9494hrhFJ60qnPZWcEFBl+bTLONfa9ISNeGryKWis2j7ANpmo7Bmwi6is3CWCxzjbVHpsI2czT7vpdLSnBKoJrjNYt/YZYzpK3aalsF"
    "dqjBdZAko0mKBQZ8IO88MSE9q0mbDLmLDEBJW+OiSbhsJMKMfpuRdKUTorjlc1SmfFg4JQXlOlXy6xZDePnhdFK62mjo3JyaGxRYCpkxyBlc7U"
    "bddxVwxWUk+LxGBT8YSVs2i5LvTaXcSWakg9+r8oRcJKXiL3MlCS1kNVdD8CWldlfD8GYtfqCH8EBMcKGX8E1K4qKd8nYpNKOdM4rklznFZloj"
    "Psisu7EF9MgCpFnJfFp48F4WWSIY1zByT7SO51k52tszVfi3hkQeA0aNdTYqei2tW4nR+hr5lc37w8LlDC9LiORWWnz5/C655/kaJke6UFJZbk"
    "V+qLLGrhfwx+176RpZYYSnN0o9r4WwffakjlyYKvjuZLfNevC6CjcB0yUZ51koZElsqWwvVLGli09vFrH1gNfUQ4uqC/DGOZToZLmC/rkODFjR"
    "vMR8filxhQNINbs5m68iDbVD2WpCsxmF8BbVy0cTRSFF3fcVRSH13dce+Ef+v2kKMYlfidJEyv9hJvOan/GGmuG1SorFKDEm6n20kCtFepiVe4"
    "HNHAHECcgfP3DK2c0mHKcC7DcfjqzFzAsDr9exYr97h059ditsntZGUzuCt3w7q2kqhIvVi6XW9/FFRVqwuC1n2vg9ztrQ6rBwXX4tZ8nfX729"
    "4L9tdQYpiUUDldbVd04zHfDf7va3ov2F9DHePN7aI9/N/b9Jj5X8N1Fw/mvp5bNIjzHuR4qd3tAiwq7SVrjbdjBGkyZ91onV4x3TXdehHQLAHN"
    "XXkn0bu0Yrn3GItl0FaL+u6/IDOroqzWtGpiUlBiU1ndbkp1z7yGezN2W+He1oGKWLvE8k47zXC1Jw9quGZDJgdNFClxE3SdOVst5bOd8rh9J0"
    "exog25WFmD39zthNf5JDljG9zcaKqyLJQ1uMAK8Z06p2lYudmUaVYy4F/tWyGzIGz1e2KZONSp2rSlL59eNKh+un5sb636wgHNkrvlMaX8MuoF"
    "GSN3gCm9WhlTej31giw5qhOeaSuwF+SJEpRX68EkfxoOvdJJLydSgptKlSkZirazto2bshR7weHsEv9XlpJPwsry2nButpV6JRaeyVoVvYJKev"
    "mL5uYirc5K6Dn2WMdHceSz+grgpzuLAB6aMuSK/dJMdcPLmEpX9aizzRoVz6Q1VxrPgfCeeuNMFxfPTuqhEuOszeJ0C4fTRZpyUXD6yO8t+M2a"
    "pHz0aWolFf6+b2zZWVC7mm161rI6d1bbZrq0dn4aj2aiO1Bgu9xQTHWltfNxYl+BbRZHLn+B7brShPMU2K7xkDsbBbYLo36gzDbj2O8vs8048v"
    "vKbLNRlj22j0O+AvettfERxCflDpgUUUZKyLblJtkK7XZX9EiRu7NNdCe2/Ah2ueTkdnLcJZKXXl+cPxI0IYBWztISkwBOxcyzUl8qEmeeAg5d"
    "96zZlWpn3hKTOpi3WApmZR84t+QuGUWtn38rVOpg4NhFc1EbE0bmYKN8Cuv+ntJUpPr5GMOlLkY+cLAMUcxwOO9hOtnJRdufiD5ycjDyTAokQF"
    "E7tXNyhUp6VuY+pLLXudni2NkiHpJAqnKQVHV1ZUNwnKeTUHohFo6J2myeGOvuawgiGFtNV3jYZ6+fQ4ePAd3qWZM76+zkY6zNfj5uNGSNjzuj"
    "3+VwksQJ1a27VzZYGWu0M4C2oy1r7Fx3gOgwlUys4aXK8ll3J1fXWm1vwHX3N17PImeDrw8MpSCouwIGZTAW8UGElSSByWH8f9/x0s22SoXnhv"
    "I4QpRYJp+S88pKJ1Va71bj9Exb8ivPzW558tLbO+KtbXWj9M96wDXhPEQ5qGfIN2EN9Uz5Hawhny2lghHss+XkMsTyrHmtTKGeMSGCEdwzp5cy"
    "g3eOfM+6cc+egskIxkc0/eTJKmQE5+OabHJlyrHC6eOy1Z6DLBE8fKcVnplaOxObeg9NSUPF9iGCpMPr+ZlPDqsb1vHin3jC/DjJWTudeFQkHL"
    "wH9oYdJWYcveJ3S+RNFMivg+kya6vBt9ykV+o4l5qPyo5EpMkUZQfblCmc7CCcInGzVmTT3UFY3hnKQivXZb7nUTgJBzM5mfDKNlI3j8abDC0B"
    "w8pPPcWUtmvONsoV5mUWQHJPLubxrDv3ZFmyw+o9uZXMIbkvl5JJZHeeHmFI1dg2WSXlM9bB1wM38DHiG26nRB5LUDUxgfF4Zoc9qYkM2bJp9l"
    "tQ6sFyV7IgY1jmThGsD192scyQFsiItU2ZBsgse3cn/zGL8q4TfHQRzliO7+D2Qt/yJ8TGmTrfEaoM5ucquJiFHLkecsofF+W+ENK+L4Sox0nI"
    "8SvH8WvF8atD/XpQzoxRvyyVTkf7ntBxX+Sqc/QaXqdPmC2Et9oyqXKZluUm8Jr2dPNd+4p937DGXst2Ah67sKCExxrXO0Ww92zveJFHmmbPrK"
    "PF3nEWXx0pBf4ET3EtW9vlaC787QiEnwQGI0lvDZE+xkfDbvhCR+6ceZOuI2tcbQyzQCnNSo/nFHA72GVncJYIdMl8yzaOte1nZkfVn8Lbnn+x"
    "a6KYkqc99U7rd5n3Yn6s8/M+tjOAf+rb5Ou1bxGaOpov0SQfAVdxYs+ZE+kIXfpFRvPjhpnFzAX9YXWVfEDoWGAf4DcasT1VGdaIeYuzhTD8BQ"
    "cPV8i12Ocvk7YnkanHIaui57S82fAoRDbCkaCeMZmgev5OsJn9sFU9UcfZ0EFj3DqCaEskuHbLtMcMM3aR9XBknK0V3QNngur359MhyOQRO5Yd"
    "UJaLbRUjgIGaJ8UIYKIESjES2KiIki8ky0QRrtzsZ6UUVwECGCnyku+aDFbKcuXEnqHiXLlutz+62YudQl258D7CuYqpol25UD9GC89WAa/chX"
    "tz1q4p16WvpnZNaThXUrum+khTkdo11WNbsHZN9QgXqF1TywJ6WR6G8ShuDRVhcoTExsexl1N3mZXsnC1cbKWGQzN1FVvJgeqekiss61ueKivV"
    "C0JtVVao3FvPMMqZK67UcZKOabtV1Q3y9A6l7r3fnZ11WboL2FkytTlKltRgaqes76LnLVlSE5YV3mpeFr7MG6o6S5bQvL+cWZyzFy6pHeWshU"
    "uqKmXDyg3llZFTzZ3hlZFT2S3elVFU9bXalRJ2/yiq8Nrpyumq8CJoWhtF2W5m3jkb7V+fqFWjb2Xc5mAM/exxDcYIOHDz7zGRcR+GIbNzySgd"
    "e+6bLYeUx59xU2zNOBNWPC4y+xw2gSDw1bkX37zg+JHxnc0h1zWGiEPQiDO+fzczsKsjgZsjzrI5wA6Rl3zDn5k29+GH519xz/7xi69f/uTDX7"
    "nPHofMWvFoF2s8Q8efB5VJuEWFEpLkeuMgXTcsoldOf4queXIDbpPslfKXyOVbLc/2Wj44os61wLU4VYLf6wQ+eez5cxNfnLxpcq9OPr3RfPPz"
    "cHOIbwDTUaPZ+Ntv//S///1b7jl88rg5N7Fd5Bq2x8GUYLuGH3xoNMc2Mr1fkjjhl0ARLwi30HUYTLw4aXLldr3emWMiCzr7v//8t9+R3n4JHz"
    "kdc/rdH6FX0xi6eNkJ/Cm5DwAddPGv/859GWIRR2LRXdQNtEggMuAgweWFZjt44A0Gg8a08RT+9RtXjfOx/dL+OXmbF85B/F4aU2zPfJ4XBhc3"
    "INcerAIHuq3NQN58cYz9L0xMHn86/0oPSfypfd0Qzo0RPxRufFLKQPQ0Ep39yvLtXxv4ir8Z4gm6BKT7DW9qg240mkPT1t7CR6DCb9wKtxrytQ"
    "mPhe2Xhdvb26YC6xUQitHMCmjiNjkfIeoN9OEyw7c5HgTNno3GvNC00BR7gxu53/iHmUX4rvQbzwE4eWzDo3H3B1ezTfJR7Td+McOX5LHTbwAS"
    "bvBCt994cff7IShzoyn1G5/bU4BiN26bMB6D4PgTGZX5+/c3t+evLY4LUbpE5uBycHF5IT194ZOD6/yl0G80Yi1c+8obvJKbSrPdVJudZrcpvR"
    "GnyOH1wcW3T0w0BC3VTOR5g9cnY7MFX7w+4Ua2Cx89bfLpjX77+uTi05uAwFf6Gxj54J2LJ4blzPz4q4YFbxp6/EWC3wzDN5/e8DyQAB28f//q"
    "jSB+ZxsW32hyDUEQXQzDrGH+8euTx+Nm49G7me2fNwTyevCHiW2CVwmdSKd9SWrJEvxscnLwQSEfAMFvF12CqLy2iOKlkchQhR7kskq5DO0Fxz"
    "2B6S4uPd4MBO9ihxHSkI4CS/TkMbx2QeBsvk9SCaGDF9hBLgL4gUH1XTSFX4AT/JsiT+ReGBzSEMxbDvJIpzB5TbFuIMvWJrjJeZjDMBLGEHMw"
    "WXD4Ozx1YP4KhU1S4KcYovDpDVGs2wCTMIwVR2boE12wLc00tLdEIdAljowg4Pi3//gd9/MZgunSffI4fBn6uzIsmMjF3/wmGL5v3j5tbJJov1"
    "0o2Nj85u1aR7odogUS3rhdsidoGygC1gItjp5D6bkNX1lvCVK9bAnPay2/vSWKRY1gUFM5P9HfbivKcta7cbE/cy3uWzpc2QS8nCcT9bMulfwY"
    "JwKOWxv5j8/cBA5eJhVUiqhgaNxhToTWZNIl7u6jR5fhBEmU51d4BG7phB8BOByb/2C2I7Zl+WYwMad+M5pS4O1PwLn9xsEWWUghIRp8mHdCwx"
    "VvQPqMNwj64Kd3v/eilY1A3uGxRRYv+xz1D39tct/NPN9evhd0tTQJMVMY2QNsDkjfCS2uhJurwRVhABm3p8HPfsjG89W7Qf+W7U6RaXyPPx++"
    "iEwL8bChK/gV58JAJh+hzWL5IQvnW+MuBxxK0+erqzerHq8SO+NXFCh9aLDBkNiK4OYQotHK958wfjuQzr2JfcU3ou8iBU/23fSV7/Zuht35C2"
    "zCesV2+caPAMZvgv4D500XbtbGYoVcMBYhKYE0vn+/JEt4erUclV1coYR548dXS7wDtoZvoQHSNOz4WH9BfMufQXtyj/XnsH5vkgfRB0hCMMgZ"
    "Xmg6Ihi0meUvxvDxZ9xPbdMP4gHECATq4mJy7tfHHI/u/gLSbFjczEOuQCzpxJ43yW8wJlybu/uLCd3CI1EkolCwGCcn8NwwikC+JY1H0MPf/v"
    "lfuBtDbwaucr/x5Zf9588bt5zNWTPTDCIIyyHbIuRtE1v6l8+Fm9Xk93KwlFJH114CgR7h4icv37//5KUIQHy8MAYEQGzanHlYH8BEClM44Ysn"
    "wpT4BQLbcw1DBl1cP3p0LZqGLpCGr4JHEIVbIdYFng4m0+cwKYVonZsYFhfY8wdLUDwfIcELZNYWRFi3WOEEGQdHmoZW7Brwvhbttz/x37+PAA"
    "PciITzZbtr0fUfPQp+wewaLIQ0GSR57QsF5t7oRW7tfzDaMCphihzyYID9u7/ACMDYk9nsO+zafRLrmcyGNndpwBfBuJA3F6Js4SuOiBQf4hpI"
    "ruF9jb7mdbKmIuLPC0CyDm3+Hs9Bqj8ZDN6ukxH2NR0Eb3xpz1ywG591pR8Hn4GrM/CceGFFM55+EjAW6J5e4On793jaml7IPWkHldwW0YjIU+"
    "ACYM+Z3f3BI0IZTONuE+ifwN9DyYev29xkSTUZGDKuhL+E3AvyISQ8GO7rAMlINBaN18SO6OdSx2IaEWKkGXd/JiGeUPfg6y9efBExnidhsaDp"
    "hx9+Tb7xuHE0QcMEJexXJzFA/7Itdnsc/4sZsjhFbcmyEIyuNgPdhq9M4tiEogB9EkgWzA8zC63Um5z6hQf+ww/EBoAEk7kkxJpMkh9+CN+/+w"
    "M3t9e++HNcpgDdJvQdAPzwwxQ8pHcz49J+BwMReFYh+fB+gHXU8DKkGd39CekGwQ/8LHCygEDiVyEThu7u9xbHe7OQp9DWDDkbvOFCH01CrRlj"
    "tysE/htYYR3oj1w8wvmFhQv8N8fFI3DMMcGLDM3zr148/4YLY42YvEz+EA4S+YAcMKfIC3DnkXf3RwIVugHKwKDpeEGiZ4xnoVUlb81RhBNooX"
    "AOf4yYD8MDzq5m6OBLwkuhfbUXAmwXscBiOiPbRFOfVUPbfDZ49aZM+0oUG8RqhswkE+V6g9DeLqwrIdxdGV13YW4Xj+Plk9WI2SYwAEtFA8WO"
    "qZbA2XtV4sEcx83xM9GZwYLhWoib3YX38/VsOsQuT6S36cGSdoAupKfPxJFhgj4QYbgmddSw++jRc+RPRDT0+OiV6A9kma1hoYWEJ5IoEWsZyV"
    "rC7E4AiCa2xv7kKXnuPxM2pXv/xLF3zgg8s7D5gIyuaIGvCW57IOQhD/zlRw/MEs9fN+cCIdH3WnP4IZy7E74xJ7EFf+nvu9GCSzj3bbA7fCOY"
    "V5YmNjQYwbTTCJZKEQY82A7eJ50+ekR+PYnhJDwl3/TrQvLNm9s3t/8PJK5dhA=="
)
SHA = "7b2991718a1e37f5a77d50c275d02b8ce73cf1b9b36c4c0c9c7f7cbd64f69568"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.67';"
V_NEW = "const APP_VERSION='v3.68';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v368.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.67 que espero (¿has pasado v367.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.68')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.67 -> v3.68')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.67 (esperaba const APP_VERSION=\'v3.67\'). Pasa v367.py primero y luego este. No toco nada.')
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

print('v3.68:')
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
