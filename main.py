import json
import sys
import threading
import ollama
import pygame

# Variables sobre la informacion del estado del pais
gobernanza = 100
economia = 100
sociedad = 100

# Estados del juego
esta_eligiendo = False
cargando_ia = False
viendo_retro = False
datos_ia = None
texto_retro = ''

# Aquí va la información de la IA
modelo = 'llama3.2:1b'

pygame.init()
screen = pygame.display.set_mode((950, 540))
pygame.display.set_caption('Presidenta de México - Simulador')
clock = pygame.time.Clock()
fuente = pygame.font.SysFont('Arial', 20)

botones_opciones = [
    pygame.Rect(100, 220, 750, 60),
    pygame.Rect(100, 300, 750, 60),
    pygame.Rect(100, 380, 750, 60),
]
boton_continuar = pygame.Rect(350, 450, 250, 50)


def generar_pregunta():
    global esta_eligiendo, cargando_ia, datos_ia

    try:
        flujo = ollama.chat(
            model=modelo,
            format='json',
            options={
                'num_predict': 250,
                'temperature': 0.7,
            },
            messages=[
                {
                    'role': 'user',
                    'content': (
                        'Eres un juego donde simulas ser presidenta de Mexico. '
                        'Genera un JSON corto con exactamente estas 3 llaves: '
                        '"situacion" (texto corto), '
                        '"opciones" (lista de 3 textos cortos), '
                        '"impacto" (lista de 3 listas de 3 numeros entre -10 y 10 para gobernanza, economia y sociedad). '
                        'Ejemplo: {"situacion": "Empezo la tercera guerra mundial, Estados Unidos te invade", "opciones": ["Haces un acuerdo", "Confrontar", "Pedir ayuda"], "impacto": [[5, -10, 10], [-5, 0, -5], [-10, 10, -15]]}'
                    ),
                }
            ],
            stream=True,
        )

        texto_completo = ''
        for respuesta in flujo:
            fragmento = respuesta['message']['content']
            texto_completo += fragmento
            print(fragmento, end='', flush=True)

        datos_ia = json.loads(texto_completo)
        print('\n\nDatos de la IA:', datos_ia, flush=True)
        esta_eligiendo = True

    except Exception as error:
        print('\nERROR en generar_pregunta:', error, flush=True)

    finally:
        cargando_ia = False


def retro_pregunta(opcion_seleccionada):
    global esta_eligiendo, cargando_ia, viendo_retro, texto_retro

    try:
        impacto_elegido = datos_ia['impacto'][opcion_seleccionada]
        flujo = ollama.chat(
            model=modelo,
            format='json',
            options={
                'num_predict': 200,
                'temperature': 0.7,
            },
            messages=[
                {
                    'role': 'user',
                    'content': (
                        f"Tenias esta situacion siendo presidenta de Mexico: {datos_ia['situacion']}. "
                        f"Resolviste con: {datos_ia['opciones'][opcion_seleccionada]}. "
                        f'Obtuviste un impacto en gobernanza, economia y sociedad de: {impacto_elegido}. '
                        f'Tus valores actuales son gobernanza={gobernanza}, economia={economia}, sociedad={sociedad}. '
                        'Genera un JSON corto con exactamente 1 llave llamada "retroalimentacion" con un texto breve explicando las consecuencias.'
                    ),
                }
            ],
            stream=True,
        )

        texto_completo = ''
        for respuesta in flujo:
            fragmento = respuesta['message']['content']
            texto_completo += fragmento
            print(fragmento, end='', flush=True)

        datos_retro = json.loads(texto_completo)
        texto_retro = datos_retro.get('retroalimentacion', 'Decisión aplicada.')
        print('\n\nRetroalimentación:', texto_retro, flush=True)
        viendo_retro = True

    except Exception as error:
        print('\nERROR en retro_pregunta:', error, flush=True)
        texto_retro = 'Se aplicaron los cambios al país.'
        viendo_retro = True

    finally:
        cargando_ia = False


while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            x, y = pygame.mouse.get_pos()

            # Paso 2: El usuario elige una respuesta
            if esta_eligiendo and not cargando_ia:
                for idx, boton in enumerate(botones_opciones):
                    if boton.collidepoint(x, y):
                        impacto = datos_ia['impacto'][idx]
                        gobernanza += impacto[0]
                        economia += impacto[1]
                        sociedad += impacto[2]

                        # Bloqueamos elección y marcamos carga ANTES de lanzar el hilo
                        esta_eligiendo = False
                        cargando_ia = True
                        hilo = threading.Thread(
                            target=retro_pregunta, args=(idx,), daemon=True
                        )
                        hilo.start()
                        break

            # Paso 3: El usuario ya leyó la retroalimentación y avanza a la siguiente pregunta
            elif viendo_retro and boton_continuar.collidepoint(x, y):
                viendo_retro = False
                datos_ia = None

    screen.fill((255, 255, 255))

    # Paso 1: Generar pregunta si no estamos cargando, ni eligiendo, ni viendo retroalimentación
    if not esta_eligiendo and not cargando_ia and not viendo_retro:
        cargando_ia = True
        hilo = threading.Thread(target=generar_pregunta, daemon=True)
        hilo.start()

    # --- DIBUJAR INTERFAZ ---
    stats = fuente.render(
        f'Gobernanza: {gobernanza}  |  Economía: {economia}  |  Sociedad: {sociedad}',
        True,
        (0, 100, 0),
    )
    screen.blit(stats, (100, 30))

    if cargando_ia:
        aviso = fuente.render('La IA está pensando...', True, (100, 100, 100))
        screen.blit(aviso, (350, 250))

    elif esta_eligiendo and datos_ia is not None:
        sit = fuente.render(
            str(datos_ia.get('situacion', ''))[:85], True, (0, 0, 0)
        )
        screen.blit(sit, (100, 130))

        opciones = datos_ia.get('opciones', [])
        for idx, boton in enumerate(botones_opciones):
            pygame.draw.rect(screen, (0, 0, 0), boton, 2)
            if idx < len(opciones):
                txt_op = fuente.render(str(opciones[idx])[:75], True, (0, 0, 0))
                screen.blit(txt_op, (boton.x + 15, boton.y + 18))

    elif viendo_retro:
        retro_render = fuente.render(texto_retro[:85], True, (0, 0, 150))
        screen.blit(retro_render, (100, 220))

        pygame.draw.rect(screen, (0, 120, 200), boton_continuar)
        txt_cont = fuente.render('Siguiente turno', True, (255, 255, 255))
        screen.blit(
            txt_cont, (boton_continuar.x + 55, boton_continuar.y + 13)
        )

    pygame.display.flip()
    clock.tick(60)