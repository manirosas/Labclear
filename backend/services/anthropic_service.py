import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Rangos de referencia por parámetro
RANGOS = {
    'glucosa':      {'nombre': 'Glucosa',           'unidad': 'mg/dL',    'min': 70,  'max': 100,  'desc': 'Azúcar en sangre en ayuno'},
    'urea':         {'nombre': 'Urea',               'unidad': 'mg/dL',    'min': 15,  'max': 45,   'desc': 'Desecho del metabolismo proteico'},
    'creatinina':   {'nombre': 'Creatinina',         'unidad': 'mg/dL',    'min': 0.6, 'max': 1.2,  'desc': 'Indicador de función renal'},
    'acido_urico':  {'nombre': 'Ácido Úrico',        'unidad': 'mg/dL',    'min': 3.5, 'max': 7.2,  'desc': 'Producto del metabolismo celular'},
    'proteinas':    {'nombre': 'Proteínas Totales',  'unidad': 'g/dL',     'min': 6.4, 'max': 8.3,  'desc': 'Proteínas en plasma sanguíneo'},
    'hemoglobina':  {'nombre': 'Hemoglobina',        'unidad': 'g/dL',     'min': 12,  'max': 17,   'desc': 'Transporta oxígeno en la sangre'},
    'leucocitos':   {'nombre': 'Leucocitos',         'unidad': 'mil/mm³',  'min': 4.5, 'max': 11,   'desc': 'Glóbulos blancos, sistema inmune'},
    'eritrocitos':  {'nombre': 'Eritrocitos',        'unidad': 'mill/mm³', 'min': 4.2, 'max': 5.9,  'desc': 'Glóbulos rojos'},
    'hematocrito':  {'nombre': 'Hematocrito',        'unidad': '%',        'min': 36,  'max': 52,   'desc': 'Proporción de glóbulos rojos'},
    'plaquetas':    {'nombre': 'Plaquetas',          'unidad': 'mil/mm³',  'min': 150, 'max': 400,  'desc': 'Coagulación sanguínea'},
    'colesterol':   {'nombre': 'Colesterol Total',   'unidad': 'mg/dL',    'min': 0,   'max': 200,  'desc': 'Lípidos totales en sangre'},
    'trigliceridos':{'nombre': 'Triglicéridos',      'unidad': 'mg/dL',    'min': 0,   'max': 150,  'desc': 'Grasas en sangre'},
    'hdl':          {'nombre': 'HDL',                'unidad': 'mg/dL',    'min': 40,  'max': 999,  'desc': 'Colesterol bueno'},
    'ldl':          {'nombre': 'LDL',                'unidad': 'mg/dL',    'min': 0,   'max': 130,  'desc': 'Colesterol malo'},
    'vldl':         {'nombre': 'VLDL',               'unidad': 'mg/dL',    'min': 0,   'max': 30,   'desc': 'Lipoproteínas de muy baja densidad'},
    'alt':          {'nombre': 'ALT (TGP)',           'unidad': 'U/L',      'min': 7,   'max': 56,   'desc': 'Enzima hepática'},
    'ast':          {'nombre': 'AST (TGO)',           'unidad': 'U/L',      'min': 10,  'max': 40,   'desc': 'Enzima hepática y muscular'},
    'bilirrubina':  {'nombre': 'Bilirrubina',        'unidad': 'mg/dL',    'min': 0.2, 'max': 1.2,  'desc': 'Producto de degradación'},
    'albumina':     {'nombre': 'Albúmina',           'unidad': 'g/dL',     'min': 3.5, 'max': 5,    'desc': 'Proteína producida por el hígado'},
}

NOMBRES_ESTUDIO = {
    'quimica':   'Química Sanguínea',
    'biometria': 'Biometría Hemática',
    'lipidico':  'Perfil Lipídico',
    'renal':     'Función Renal',
    'hepatica':  'Función Hepática',
}

def calcular_estado(valores):
    """
    Determina el estado general del análisis:
    - 'normal'    → todos los valores en rango
    - 'precaucion'→ 1-2 valores fuera de rango
    - 'alerta'    → 3 o más valores fuera de rango
    """
    fuera = 0
    for param, valor in valores.items():
        rango = RANGOS.get(param)
        if rango and (valor < rango['min'] or valor > rango['max']):
            fuera += 1
    if fuera == 0:
        return 'normal'
    elif fuera <= 2:
        return 'precaucion'
    else:
        return 'alerta'

def analizar_con_ia(tipo_estudio, valores, sexo=None, fecha_nac=None):
    """
    Llama a Claude para interpretar los resultados del laboratorio.
    Retorna el texto de la respuesta.
    """
    nombre_estudio = NOMBRES_ESTUDIO.get(tipo_estudio, tipo_estudio)

    # Construir lista de parámetros con su estado
    lineas_params = []
    for param, valor in valores.items():
        rango = RANGOS.get(param)
        if rango:
            if valor < rango['min']:
                estado_param = f"BAJO (referencia: {rango['min']}–{rango['max']} {rango['unidad']})"
            elif valor > rango['max']:
                estado_param = f"ALTO (referencia: {rango['min']}–{rango['max']} {rango['unidad']})"
            else:
                estado_param = f"normal (referencia: {rango['min']}–{rango['max']} {rango['unidad']})"
            lineas_params.append(f"- {rango['nombre']}: {valor} {rango['unidad']} → {estado_param}")
        else:
            lineas_params.append(f"- {param}: {valor}")

    # Info del paciente si está disponible
    info_paciente = ''
    if sexo:
        info_paciente += f"Sexo biológico: {'Masculino' if sexo == 'M' else 'Femenino'}. "
    if fecha_nac:
        try:
            from datetime import date
            nac = date.fromisoformat(str(fecha_nac))
            edad = (date.today() - nac).days // 365
            info_paciente += f"Edad aproximada: {edad} años."
        except Exception:
            pass

    prompt = f"""Eres el asistente médico educativo de LabClear, una plataforma de salud mexicana.
Tu rol es ayudar a las personas a entender sus resultados de laboratorio en lenguaje sencillo y claro, sin emitir diagnósticos.

{'Información del paciente: ' + info_paciente if info_paciente else ''}

Tipo de estudio: {nombre_estudio}

Resultados obtenidos:
{chr(10).join(lineas_params)}

Por favor:
1. Explica brevemente (1-2 oraciones) qué mide cada parámetro que esté FUERA de rango normal, en palabras simples.
2. Da un resumen general de 2-3 líneas sobre el estado del análisis.
3. Indica qué hábitos o situaciones pueden relacionarse con los valores alterados (si los hay).
4. Recuerda al final que esta información es educativa y que deben consultar a su médico.

Usa un tono amigable, empático y accesible. Evita tecnicismos innecesarios.
Si todos los valores están normales, felicita al usuario y motívalo a seguir con sus hábitos saludables."""

    mensaje = client.messages.create(
        model='claude-sonnet-4-20250514',
        max_tokens=1500,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return mensaje.content[0].text