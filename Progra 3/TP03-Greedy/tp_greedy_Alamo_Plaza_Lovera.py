import json
import math
from pathlib import Path

from g1_student_api import RobotG1


def cargar_mapa(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        mapa = json.load(archivo)

    validar_mapa(mapa)

    return mapa


def validar_mapa(mapa):
    campos_obligatorios = [
        "nombre",
        "grilla",
        "inicio",
        "destino",
        "tamano_celda_metros",
        "orientacion_inicial",
        "maximo_pasos"
    ]

    for campo in campos_obligatorios:
        if campo not in mapa:
            raise ValueError(
                f"Falta el campo obligatorio '{campo}' en el archivo JSON."
            )

    grilla = mapa["grilla"]

    if len(grilla) == 0:
        raise ValueError("La grilla no puede estar vacía.")

    cantidad_columnas = len(grilla[0])

    for fila in grilla:
        if len(fila) != cantidad_columnas:
            raise ValueError(
                "Todas las filas de la grilla deben tener el mismo tamaño."
            )

        for celda in fila:
            if celda not in [0, 1, 2]:
                raise ValueError(
                    "La grilla solamente puede contener valores 0, 1 o 2."
                )

    inicio = mapa["inicio"]
    destino = mapa["destino"]

    if len(inicio) != 2 or len(destino) != 2:
        raise ValueError(
            "Inicio y destino deben tener formato [fila, columna]."
        )

    filas = len(grilla)
    columnas = len(grilla[0])

    if (
        inicio[0] < 0
        or inicio[0] >= filas
        or inicio[1] < 0
        or inicio[1] >= columnas
    ):
        raise ValueError("La posición inicial está fuera de la grilla.")

    if (
        destino[0] < 0
        or destino[0] >= filas
        or destino[1] < 0
        or destino[1] >= columnas
    ):
        raise ValueError("La posición destino está fuera de la grilla.")

    orientaciones_validas = [
        "NORTE",
        "ESTE",
        "SUR",
        "OESTE"
    ]

    if mapa["orientacion_inicial"] not in orientaciones_validas:
        raise ValueError("La orientación inicial no es válida.")

    if mapa["tamano_celda_metros"] <= 0:
        raise ValueError(
            "El tamaño de la celda debe ser mayor a cero."
        )

    if mapa["maximo_pasos"] <= 0:
        raise ValueError(
            "El máximo de pasos debe ser mayor a cero."
        )


def distancia_manhattan(posicion, destino):
    fila = posicion[0]
    columna = posicion[1]

    fila_destino = destino[0]
    columna_destino = destino[1]

    distancia = (
        abs(fila - fila_destino)
        + abs(columna - columna_destino)
    )

    return distancia


def generar_candidatos(posicion):
    fila = posicion[0]
    columna = posicion[1]

    # Criterio de desempate:
    # ARRIBA -> DERECHA -> ABAJO -> IZQUIERDA
    candidatos = [
        [fila - 1, columna],      # ARRIBA
        [fila, columna + 1],      # DERECHA
        [fila + 1, columna],      # ABAJO
        [fila, columna - 1]       # IZQUIERDA
    ]

    return candidatos


def es_factible(candidato, grilla, visitados):
    fila = candidato[0]
    columna = candidato[1]

    # Fuera de la grilla
    if fila < 0 or fila >= len(grilla):
        return False

    if columna < 0 or columna >= len(grilla[0]):
        return False

    # Obstáculo
    if grilla[fila][columna] == 1:
        return False

    # Zona prohibida
    if grilla[fila][columna] == 2:
        return False

    # Posición ya visitada
    if candidato in visitados:
        return False

    return True


def seleccionar_mejor_candidato(candidatos_validos, destino):
    mejor_candidato = candidatos_validos[0]

    menor_distancia = distancia_manhattan(
        mejor_candidato,
        destino
    )

    for candidato in candidatos_validos:
        distancia = distancia_manhattan(
            candidato,
            destino
        )

        # Si hay empate no se reemplaza.
        # Se conserva el orden:
        # ARRIBA -> DERECHA -> ABAJO -> IZQUIERDA
        if distancia < menor_distancia:
            mejor_candidato = candidato
            menor_distancia = distancia

    return mejor_candidato


def resolver_greedy(mapa):
    grilla = mapa["grilla"]
    inicio = mapa["inicio"]
    destino = mapa["destino"]
    maximo_pasos = mapa["maximo_pasos"]

    posicion_actual = inicio

    ruta = [inicio]
    visitados = [inicio]

    pasos = 0

    while pasos < maximo_pasos:

        if posicion_actual == destino:
            return "DESTINO_ALCANZADO", ruta, pasos

        candidatos = generar_candidatos(
            posicion_actual
        )

        candidatos_validos = []

        for candidato in candidatos:
            if es_factible(
                candidato,
                grilla,
                visitados
            ):
                candidatos_validos.append(
                    candidato
                )

        if len(candidatos_validos) == 0:
            return "BLOQUEADO", ruta, pasos

        mejor_candidato = seleccionar_mejor_candidato(
            candidatos_validos,
            destino
        )

        posicion_actual = mejor_candidato

        ruta.append(posicion_actual)
        visitados.append(posicion_actual)

        pasos += 1

        print(
            "Paso",
            pasos,
            "- Posición:",
            posicion_actual,
            "- Distancia:",
            distancia_manhattan(
                posicion_actual,
                destino
            )
        )

        # Controlar nuevamente después de avanzar.
        if posicion_actual == destino:
            return "DESTINO_ALCANZADO", ruta, pasos

    return "LIMITE_DE_PASOS", ruta, pasos


def obtener_direccion(origen, destino):
    diferencia_fila = (
        destino[0] - origen[0]
    )

    diferencia_columna = (
        destino[1] - origen[1]
    )

    if diferencia_fila == -1:
        return "NORTE"

    if diferencia_columna == 1:
        return "ESTE"

    if diferencia_fila == 1:
        return "SUR"

    if diferencia_columna == -1:
        return "OESTE"


def traducir_ruta_a_instrucciones(
    ruta,
    orientacion_inicial,
    tamano_celda
):
    instrucciones = []

    orientacion_actual = orientacion_inicial

    orientaciones = [
        "NORTE",
        "ESTE",
        "SUR",
        "OESTE"
    ]

    for i in range(len(ruta) - 1):
        posicion_actual = ruta[i]
        siguiente_posicion = ruta[i + 1]

        direccion_necesaria = obtener_direccion(
            posicion_actual,
            siguiente_posicion
        )

        indice_actual = orientaciones.index(
            orientacion_actual
        )

        indice_necesario = orientaciones.index(
            direccion_necesaria
        )

        diferencia = (
            indice_necesario - indice_actual
        ) % 4

        if diferencia == 1:
            instrucciones.append(
                "GIRAR DERECHA 90°"
            )

        elif diferencia == 2:
            instrucciones.append(
                "GIRAR 180°"
            )

        elif diferencia == 3:
            instrucciones.append(
                "GIRAR IZQUIERDA 90°"
            )

        instrucciones.append(
            f"AVANZAR {tamano_celda:.2f} m"
        )

        orientacion_actual = direccion_necesaria

    return instrucciones


def obtener_causa_finalizacion(resultado):
    if resultado == "DESTINO_ALCANZADO":
        return "El robot llegó a la celda destino."

    if resultado == "BLOQUEADO":
        return (
            "No existen candidatos válidos "
            "para continuar."
        )

    if resultado == "LIMITE_DE_PASOS":
        return (
            "Se alcanzó el máximo de pasos "
            "permitido."
        )


def ejecutar_instrucciones_robot(instrucciones):
    robot = RobotG1()

    # Velocidad utilizada para avanzar.
    velocidad_avance = 0.25

    # pi/4 rad/s = 45 grados por segundo.
    velocidad_giro = math.pi / 4

    print()
    print("Conectando con el simulador G1...")

    try:
        estado_inicial = robot.conectar()

        print("Estado inicial:")
        print(estado_inicial)
        print()

        for instruccion in instrucciones:

            print(
                "Ejecutando en simulador:",
                instruccion
            )

            if instruccion.startswith("AVANZAR"):
                partes = instruccion.split()

                distancia = float(partes[1])

                # tiempo = distancia / velocidad
                tiempo = (
                    distancia
                    / velocidad_avance
                )

                estado = robot.movimiento(
                    adelante=velocidad_avance,
                    costado=0.0,
                    giro=0.0,
                    tiempo=tiempo
                )

            elif instruccion == "GIRAR DERECHA 90°":
                estado = robot.movimiento(
                    adelante=0.0,
                    costado=0.0,
                    giro=-velocidad_giro,
                    tiempo=2.0
                )

            elif instruccion == "GIRAR IZQUIERDA 90°":
                estado = robot.movimiento(
                    adelante=0.0,
                    costado=0.0,
                    giro=velocidad_giro,
                    tiempo=2.0
                )

            elif instruccion == "GIRAR 180°":
                estado = robot.movimiento(
                    adelante=0.0,
                    costado=0.0,
                    giro=velocidad_giro,
                    tiempo=4.0
                )

            print(
                "Estado:",
                estado
            )

        robot.detenerse()

        print()
        print("Estado final:")
        print(
            robot.verificar_estado()
        )

    except RuntimeError as error:
        print()
        print(
            "ERROR AL CONECTAR CON EL SIMULADOR:"
        )
        print(error)

    finally:
        if robot.conectado:
            robot.detenerse()
            robot.desconectar()


def main():
    carpeta_actual = (
        Path(__file__).resolve().parent
    )

    print(
        "Seleccione el mapa que desea ejecutar:"
    )

    print(
        "1 - Mapa 1 - Solución directa"
    )

    print(
        "2 - Mapa 2 - Solución no óptima"
    )

    print(
        "3 - Mapa 3 - Fracaso de la estrategia"
    )

    print()

    opcion = input(
        "Ingrese una opción (1, 2 o 3): "
    )

    if opcion == "1":
        nombre_archivo = "mapa1.json"

    elif opcion == "2":
        nombre_archivo = "mapa2.json"

    elif opcion == "3":
        nombre_archivo = "mapa3.json"

    else:
        print("Opción inválida.")
        return

    ruta_mapa = (
        carpeta_actual
        / "mapas"
        / nombre_archivo
    )

    mapa = cargar_mapa(
        ruta_mapa
    )

    print()
    print("Nombre:", mapa["nombre"])
    print("Inicio:", mapa["inicio"])
    print("Destino:", mapa["destino"])

    print(
        "Tamaño de celda:",
        mapa["tamano_celda_metros"],
        "m"
    )

    print(
        "Orientación inicial:",
        mapa["orientacion_inicial"]
    )

    print(
        "Máximo de pasos:",
        mapa["maximo_pasos"]
    )

    print()

    resultado, ruta, pasos = resolver_greedy(
        mapa
    )

    causa = obtener_causa_finalizacion(
        resultado
    )

    print()
    print("Resultado:", resultado)
    print("Causa:", causa)

    print(
        "Cantidad de movimientos:",
        pasos
    )

    print(
        "Ruta recorrida:",
        ruta
    )

    instrucciones = traducir_ruta_a_instrucciones(
        ruta,
        mapa["orientacion_inicial"],
        mapa["tamano_celda_metros"]
    )

    print()
    print(
        "Instrucciones para el robot:"
    )

    for instruccion in instrucciones:
        print(
            "-",
            instruccion
        )

    print()

    ejecutar = input(
        "¿Desea ejecutar la ruta en el simulador? (S/N): "
    ).strip().upper()

    if ejecutar == "S":
        ejecutar_instrucciones_robot(
            instrucciones
        )

    else:
        print(
            "La ruta no se ejecutará en el simulador."
        )


if __name__ == "__main__":
    main()