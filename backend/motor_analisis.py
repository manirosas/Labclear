# motor_analisis.py
# Lee parametros y rangos desde MySQL en lugar de tenerlos hardcodeados.

NOMBRES_ESTUDIO = {
    'quimica':   'Quimica Sanguinea',
    'biometria': 'Biometria Hematica',
    'lipidico':  'Perfil Lipidico',
    'renal':     'Funcion Renal',
    'hepatica':  'Funcion Hepatica',
}

CONDICIONES = ['diabetes', 'embarazo', 'hipertension', 'dislipidemia', 'anemia', 'enfermedad_renal']


def _condiciones_activas(antecedentes):
    return [c for c in CONDICIONES if antecedentes.get(c)]


def _buscar_rango(cursor, parametro_id, condiciones):
    for condicion in condiciones:
        cursor.execute(
            '''SELECT min_val, max_val, texto_normal, texto_alto, texto_bajo
               FROM rangos_condicion
               WHERE parametro_id = %s AND condicion = %s''',
            (parametro_id, condicion)
        )
        rango = cursor.fetchone()
        if rango:
            return rango
    cursor.execute(
        '''SELECT min_val, max_val, texto_normal, texto_alto, texto_bajo
           FROM rangos_base WHERE parametro_id = %s''',
        (parametro_id,)
    )
    return cursor.fetchone()


def interpretar_valor(cursor, param_clave, valor, condiciones):
    cursor.execute('SELECT id, nombre, unidad FROM parametros WHERE clave = %s', (param_clave,))
    param = cursor.fetchone()
    if not param:
        return None
    rango = _buscar_rango(cursor, param['id'], condiciones)
    if not rango:
        return None
    min_val = float(rango['min_val'])
    max_val = float(rango['max_val'])
    if valor < min_val:
        estado = 'bajo'
        texto  = rango['texto_bajo'] or ''
    elif valor > max_val:
        estado = 'alto'
        texto  = rango['texto_alto'] or ''
    else:
        estado = 'normal'
        texto  = rango['texto_normal'] or ''
    return {
        'estado': estado, 'explicacion': texto,
        'min': min_val, 'max': max_val,
        'nombre': param['nombre'], 'unidad': param['unidad'],
    }


def calcular_estado(cursor, valores, condiciones):
    fuera = 0
    for clave, valor in valores.items():
        r = interpretar_valor(cursor, clave, valor, condiciones)
        if r and r['estado'] != 'normal':
            fuera += 1
    if fuera == 0:   return 'normal'
    elif fuera <= 2: return 'precaucion'
    else:            return 'alerta'


def generar_resumen(cursor, tipo_estudio, valores, antecedentes=None):
    if antecedentes is None:
        antecedentes = {}
    condiciones    = _condiciones_activas(antecedentes)
    nombre_estudio = NOMBRES_ESTUDIO.get(tipo_estudio, tipo_estudio)
    lineas         = []
    fuera_de_rango = []
    normales       = []

    for clave, valor in valores.items():
        r = interpretar_valor(cursor, clave, valor, condiciones)
        if not r:
            continue
        if r['estado'] != 'normal':
            fuera_de_rango.append(r | {'valor': valor})
        else:
            normales.append(r['nombre'])

    lineas.append(f"Interpretacion de tu {nombre_estudio}\n")

    if condiciones:
        etiquetas = {
            'diabetes': 'Diabetes', 'embarazo': 'Embarazo',
            'hipertension': 'Hipertension', 'dislipidemia': 'Colesterol alto',
            'anemia': 'Anemia', 'enfermedad_renal': 'Enfermedad renal',
        }
        lineas.append("Esta interpretacion fue personalizada considerando: "
                      + ', '.join(etiquetas.get(c, c) for c in condiciones) + ".\n")

    if fuera_de_rango:
        lineas.append("Valores que requieren atencion:\n")
        for item in fuera_de_rango:
            d = 'ALTO' if item['estado'] == 'alto' else 'BAJO'
            lineas.append(f"- {item['nombre']}: {item['valor']} {item['unidad']} ({d})")
            if item['explicacion']:
                lineas.append(f"  {item['explicacion']}\n")
    else:
        lineas.append("Todos tus valores se encuentran dentro del rango normal para tu perfil.\n")

    if normales:
        lineas.append(f"Valores en rango normal: {', '.join(normales)}.\n")

    n = len(fuera_de_rango)
    t = len(valores)
    if n == 0:
        lineas.append("Resumen: Tu analisis muestra resultados dentro de los parametros normales. "
                      "Continua con tus habitos y revisiones periodicas.")
    elif n <= 2:
        lineas.append(f"Resumen: De {t} parametros evaluados, {n} se encuentra(n) fuera del rango. "
                      "Te recomendamos comentarlo con tu medico.")
    else:
        lineas.append(f"Resumen: Se encontraron {n} valores fuera del rango normal. "
                      "Es recomendable que acudas con tu medico para una evaluacion completa.")

    lineas.append("\nAviso: Esta informacion es unicamente orientativa y educativa. "
                  "No reemplaza el diagnostico de un profesional de la salud. "
                  "Ante cualquier duda, consulta a tu medico.")
    return '\n'.join(lineas)