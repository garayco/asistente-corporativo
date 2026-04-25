from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

# Configuración inicial
URL_INICIAL = "https://www.tqconfiable.com/"
MAX_PAGINAS = 30
TIMEOUT = (10, 20)
MAX_REDIRECCIONES = 5
HEADERS = {"User-Agent": "Mozilla/5.0"}

def normalizar_url(base, href, dominio_permitido, host_canonico):
    # Normaliza una URL relativa a absoluta y verifica si es válida
    if not href:
        return None

    href = href.strip()
    # Ignorar enlaces no válidos
    if href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return None

    # Convertir a URL absoluta
    absoluta = urljoin(base, href)
    parseada = urlparse(absoluta)
    # Solo permitir HTTP/HTTPS
    if parseada.scheme not in ("http", "https"):
        return None

    # Verificar dominio
    dominio_actual = parseada.netloc.lower().removeprefix("www.")
    if dominio_actual != dominio_permitido:
        return None

    # Conservar la ruta tal como viene
    ruta = parseada.path or "/"
    # Devolver URL normalizada
    return urlunparse(("https", host_canonico, ruta, "", parseada.query, ""))

def descargar_pagina(session, url_inicial, dominio_permitido, host_canonico):
    # Sigue redirecciones manualmente para forzar HTTPS en el mismo dominio.
    url_actual = url_inicial
    redirecciones_vistas = set()

    for _ in range(MAX_REDIRECCIONES + 1):
        respuesta = session.get(url_actual, timeout=TIMEOUT, allow_redirects=False)

        if not respuesta.is_redirect and not respuesta.is_permanent_redirect:
            respuesta.raise_for_status()
            return respuesta, url_actual

        destino_crudo = respuesta.headers.get("Location")
        destino = normalizar_url(
            url_actual, destino_crudo, dominio_permitido, host_canonico
        )
        respuesta.close()

        if not destino:
            raise requests.RequestException(
                f"Redirección descartada desde {url_actual} hacia {destino_crudo!r}"
            )

        if destino in redirecciones_vistas:
            raise requests.TooManyRedirects(
                f"Bucle de redirección detectado hacia {destino}"
            )

        redirecciones_vistas.add(destino)
        print(f"Redirigida a: {destino}")
        url_actual = destino

    raise requests.TooManyRedirects(
        f"Se excedió el máximo de redirecciones para {url_inicial}"
    )

def extraer_enlaces(url_inicial):
    # Extrae enlaces internos del sitio web usando BFS
    host_canonico = urlparse(url_inicial).netloc.lower()
    dominio = host_canonico.removeprefix("www.")
    visitados = set()
    en_cola = {url_inicial}
    por_visitar = deque([url_inicial])
    total_encontrados = 0

    # Crear sesión para reutilizar conexiones
    session = requests.Session()
    session.headers.update(HEADERS)

    # Abrir archivo para guardar las URLs extraídas
    with open("output/extracted_urls.txt", "w", encoding="utf-8") as archivo_urls:
        while por_visitar and len(visitados) < MAX_PAGINAS:
            url_actual = por_visitar.popleft()
            en_cola.discard(url_actual)

            if url_actual in visitados:
                continue

            print(f"\nVisitando: {url_actual}")

            try:
                respuesta, url_final = descargar_pagina(
                    session, url_actual, dominio, host_canonico
                )
            except requests.RequestException as error:
                print(f"Error en {url_actual}: {error}")
                visitados.add(url_actual)
                continue

            visitados.add(url_actual)
            if url_final != url_actual:
                print(f"Página final: {url_final}")
                visitados.add(url_final)

            soup = BeautifulSoup(respuesta.text, "html.parser")
            respuesta.close()

            nuevos_enlaces = 0
            for enlace in soup.find_all("a", href=True):
                url_normalizada = normalizar_url(
                    url_final, enlace["href"], dominio, host_canonico
                )
                if not url_normalizada:
                    continue

                if url_normalizada in visitados or url_normalizada in en_cola:
                    continue

                por_visitar.append(url_normalizada)
                en_cola.add(url_normalizada)
                total_encontrados += 1
                nuevos_enlaces += 1
                print(f"Encontrada: {url_normalizada}")
                archivo_urls.write(url_normalizada + "\n")

            if nuevos_enlaces == 0:
                print("No se encontraron enlaces internos nuevos en esta página.")

        print(
            f"\nResumen: {len(visitados)} páginas visitadas, "
            f"{total_encontrados} enlaces internos encontrados."
        )

extraer_enlaces(URL_INICIAL)
