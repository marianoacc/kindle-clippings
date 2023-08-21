#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import json
import os
import re
import argparse
import pprint

BOUNDARY = u"==========\r\n"
DATA_FILE = u"clips.json"
OUTPUT_DIR = u"output"
MIDEBUG = 2
MIDEBUGRES = 'N'
MIMARKUSERNOTE = 'USER NOTE:'

def get_sections(filename):
    with open(filename, 'rb') as f:
        content = f.read().decode('utf-8')
    content = content.replace(u'\ufeff', u'')
    return content.split(BOUNDARY)


def get_clip(section, mionlynotes=0,mikeynotes='not'):
    clip = {}
    lines = [l for l in section.split(u'\r\n') if l]
    #
    #
    if len(lines) != 3 :
       return
  
    if MIDEBUG > 2:
        print_clip(lines)

    clip['book'] = lines[0]
    #match = re.search(r'(\d+)-\d+', lines[1])
    match = re.search(r'(\d+)(?:-(\d+))?', lines[1])
    # esta expresión intenta encontrar el tipico formato  de los subrayados nnn-nnn
    # la limitación que tiene esto es que no permite extraer las notes 
    # que vienen en un string como el siguiente: "- La nota en la página 89 | Añadido "
    # para hacerlo valido para cualquier idioma, si no se encontraron
    # las paginas del subrayado buca un numero seguido de un pipe
    # trato de capturar el numero para ordenar las notes junto con los subrayados a 
    # lo largo del texto y que no queden en cualquier lado
    position = match.group(1)
    clip['position'] = int(position)
    mipagina = apaExtraePagina(lines[1])
    miautor = apaExtraeAutor(lines[0])
    miano = apaExtraeAno(lines[0])
    minote = extraeNotaUsuario(lines[1],mikeynotes)
    clip['content'] = minote + lines[2] + miautor + miano + mipagina
#   print (clip['content'])
    return clip

def apaExtraePagina(lineaPagina):
    # En esta rutina debo buscar dos tipos de secuencia
    # la tipica del subrayado nnn-nnn |
    # o la tipica de las notes  nnn |
    #
    # Voy a utilizar una primera expresion regular para reemplazar toda la 
    # sentencia lo subrayado en la pagina, pero tratando de hacerlo neutral al idioma
    # para lo que voy a reemplazar todo lo anterior a los dígitos, quedándome con el grupo
    #
    # 
    #
    #
    mitransform = ''
    #  expresión para reemplazar todo lo anterior de los digitos
    #mipatron = re.compile(r'.*?(\d+(?:-\d*))?')
    #mipatron = re.compile(r'.*?(\d+(?:-\d*))?\s*\|')
    mipatron = re.compile(r'(\d+)(?:-(\d+))?')
    mimatch = mipatron.search(lineaPagina)
    if mimatch:
       mitransform = mimatch.group(1)
       mistart = mimatch.group(1)
       miend = mimatch.group(2)
       if mistart == miend or miend is None:
           mitransform = re.sub(mipatron, 'p. ' + mistart + ')' ,mitransform, re.UNICODE)
       else:
           mitransform = re.sub(mipatron, 'pp. ' + mistart + '-' + miend + ')' ,mitransform, re.UNICODE)
    return mitransform

def extraeNotaUsuario(lineaPagina,mikeynotes):
    minote = ''
    # Primera expresión para ver si se trata de una nota o subrayado

    mipatron = re.compile(mikeynotes + r'.*\d+\s*\|')
    mimatch = mipatron.search(lineaPagina)
    if mimatch:
        minote = MIMARKUSERNOTE + ' '
    return minote

def apaExtraeAno(lineaAutor):
    mitransform='miano, '
    miconano=1
    if miconano == 1:
       mipatron = re.compile(r'\((\d{4})\)')
       mimatch = mipatron.search(lineaAutor)
       if mimatch:
           mitransform = mimatch.group(1) + ', '
    return mitransform

def apaExtraeAutor(lineaAutor):
    mitransform=' (<miautor>, <miano>, '
    miconautor=1
    if miconautor == 1:
       mipatron = re.compile(ur"^(.*?) - (.*)$", re.UNICODE)
       mimatch = mipatron.match(lineaAutor)
       if mimatch:
           mitransform=' (' + mimatch.group(1) + ', '
    return mitransform

def export_txt(clips):
    """
    Export each book's clips to single text.
    """
    for book in clips:
        lines = []
        for pos in sorted(clips[book]):
            lines.append(clips[book][pos].encode('utf-8'))

        filename = os.path.join(OUTPUT_DIR, u"%s.md" % book)
        with open(filename, 'wb') as f:
            f.write("\n\n---\n\n".join(lines))

def load_clips():
    """
    Load previous clips from DATA_FILE
    """
    try:
        with open(DATA_FILE, 'rb') as f:
            return json.load(f)
    except (IOError, ValueError):
        return {}


def save_clips(clips):
    """
    Save new clips to DATA_FILE
    """
    with open(DATA_FILE, 'wb') as f:
        json.dump(clips, f)

def print_clip(lines):
# Solo utilizado para mostrar en debug el contenido parseado
    print ('-------------------------------------- linea 0 ---------------------------------------------')
    print (lines[0])
    print ('-------------------------------------- linea 1 ---------------------------------------------')
    print (lines[1])
    print ('-------------------------------------- linea 2 ---------------------------------------------')
    print (lines[2])
    print MIDEBUGRES
    mi_debug_key_wait()

def mi_debug_key_wait(r='N'):
    global  MIDEBUGRES
    if MIDEBUGRES == 'N':
        r=raw_input('Resume? (Y/N)')
        if r == 'Y':
            MIDEBUGRES = 'Y'
    return r

def mi_debug(mensaje='debug call', levelinf=0, keywait=0):
    if MIDEBUG > levelinf:
        print (mensaje)
    if keywait:
        mi_debug_key_wait()
    return mensaje

def main():

    global MIMARKUSERNOTE

    # 
    miparse=argparse.ArgumentParser(description='Requiere pasar el mifilterbook y si es solo notes, ambos son optativos')
    miparse.add_argument('--book', type=str, default=None, help='Cadena de caracteres que identifique univocamente un libro')
    miparse.add_argument('--annotations', action='store_true', help='Extraer solo las notas')
    miparse.add_argument('--keywordnote', type=str, default='not', help='Cadena de caracteres que identifica las notas de acuerdo a idioma kindle')
    miparse.add_argument('--markusernote', type=str, default='USER NOTE:', help='String para destacar notas de usuario sobre subrayado')
    miparse.add_argument('--debug', type=int, default=0, help='Nivel de debug (0-1-2-3)')
    miargs=miparse.parse_args()
    mifilterbook = miargs.book
    mionlynotes = miargs.annotations
    mikeynotes = miargs.keywordnote
    MIMARKUSERNOTE = miargs.markusernote
    mi_debug(miargs,1)

    # load old clips

    clips = collections.defaultdict(dict)
# POR AHORA NO    clips.update(load_clips())
    # extract clips
    sections = get_sections(u'My Clippings.txt')
    misections = sections
    mi_debug(sections,2,1)
    for section in sections:
        clip = get_clip(section,mionlynotes,mikeynotes)
        if clip:
            if mifilterbook is None and not mionlynotes:
                # no filter
                mi_debug('No filters sets', 0)
                clips[clip['book']][str(clip['position'])] = clip['content']
            elif mifilterbook is not None and not mionlynotes:                
                # filter by book only
                mi_debug('Filter by book:' + mifilterbook, 0)
                mipatron = re.compile(ur'.*' + mifilterbook + r'.*', re.UNICODE)
                mi_debug(clip['book'],2,1)
                if mipatron.match(clip['book']):
                    mi_debug('Filter by book:' + mifilterbook + ' MATCH' , 1, 1)
                    clips[clip['book']][str(clip['position'])] = clip['content']
            elif mifilterbook is None and mionlynotes:                
                # filter by notes only
                mi_debug('Filter by notes with string:' + mikeynotes, 0)
                #mipatron = re.compile(ur'.*' + mikeynotes + r'.*\d+\s*\|', re.UNICODE)
                mipatron = re.compile(ur'^' + MIMARKUSERNOTE  + '.*' , re.UNICODE)
                mi_debug(clip['content'],2,1)
                if mipatron.match(clip['content']):
                    mi_debug('Filter by notes with string:' + mikeynotes + ' MATCH' , 1, 1)
                    clips[clip['book']][str(clip['position'])] = clip['content']
            elif mifilterbook is not None and mionlynotes:                
                # filter by notes and book
                mi_debug('Filter by book: ' + mifilterbook + ' and notes with string: ' + mikeynotes, 0)
                mipatron = re.compile(ur'.*' + mifilterbook + r'.*', re.UNICODE)
                if mipatron.match(clip['book']):
                    mi_debug('Filter by book: ' + mifilterbook  + ' MATCH PARTIAL' , 1, 1)
                    #mipatron = re.compile(ur'.*' + mikeynotes + r'.*\d+\s*\|', re.UNICODE)
                    mipatron = re.compile(ur'^' + MIMARKUSERNOTE  + '.*' , re.UNICODE)
                    mi_debug(clip['content'],1,1)
                    if mipatron.match(clip['content']):
                        mi_debug('Filter by notes with string:' + mikeynotes + 'MATCH FULL',1,1 )
                        clips[clip['book']][str(clip['position'])] = clip['content']
 
    
    # remove key with empty value
    clips = {k: v for k, v in clips.items() if v}

    misclips = clips
    if MIDEBUG > 2:
        pp=pprint.PrettyPrinter()
        pp.pprint(clips)
        r=raw_input('Continue...')

#    if mifilterbook is not None:
#        mipatron = re.compile(r'.*' + mifilterbook + r'.*')
#        misclips = {filter(lambda misitems: mipatron.match(misitems),clips)
#    if mionlynotes:
#        mipatron = re.compile(mikeynotes + r'.*\d+\s*\|')
#        misclips = filter(lambda misitems:mipatron.search(misitems),clips)
#        if not match:
#           print ('entro en not match notes')
#           return

    # save/export clips
    save_clips(misclips)
    export_txt(misclips)


if __name__ == '__main__':
    main()

