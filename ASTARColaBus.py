#!usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
import operator
import time
import re


class Alumno:
    """Clase que define los atributos necesario para representar un alumno"""

    def __init__(self, id, conflictivo, movilidad, asiento):
        self.id = id  # Identificador asignado al alumno
        self.conflictivo = conflictivo  # Atributo que indica si un alumno es conflictivo o no 'C'/'X'
        self.movilidad = movilidad  # Atributo que indica si un alumno es de movilidad reducida o no 'R'/'X'
        self.asiento = asiento  # Valor que indica que asiento ocupa el alumno

    def __repr__(self):  # Representacion del alumno al imprimir el objeto
        return f"({self.id}:{self.conflictivo},{self.movilidad},{self.asiento})"

    def __eq__(self, other):
        return self.id == other.id  # Para comparar dos objetos alumno comparamos sus id's


class Nodo:
    """Clase que define como ha de ser un nodo para nuestra busqueda"""

    def __init__(self, nodo_padre, alumnos_sin_asignar, alumnos_asignados, g, h):
        self.alumnos_sin_asignar = alumnos_sin_asignar  # Lista alumnos sin asignar
        self.alumnos_asignados = alumnos_asignados  # Lista de alumnos asignados
        self.h = h  # Heuristica
        self.g = g  # Coste real
        self.nodo_padre = nodo_padre  # Objeto nodo del que desciende el nodo

    def evaluacion(self):
        """Calcula el valor de f"""
        return self.g + self.h  # Metodo que devuelve el valor f del nodo

    def __repr__(self):
        return str(f"{self.alumnos_asignados},g:{self.g},h:{self.h},f:{self.evaluacion()}")

    def __eq__(self, other):
        if self.alumnos_asignados == other.alumnos_asignados:  # si dos nodos tienen la misma cola se consideran iguales
            return True
        return False


class AStar:
    """Clase encargada de la búsqueda usando el algoritmo A*"""

    def __init__(self, path, path_alumnos, tipo_heuristica):
        self.heuristica = tipo_heuristica  # Tipo de heuristica a usar por el algoritmo
        self.path = os.path.abspath(path)  # Path absoluto al directorio de los ficheros de pruebas
        self.path_alumnos = self.path + "/" + path_alumnos  # Path hasta el fichero de alumnos
        self.nombre_fichero_alumnos = self.path + "/" + path_alumnos.split('.')[0]  # Para el nombre del fichero de salida
        self.alumnos = self.leerFicheroAlumnos()  # Se saca la lista de alumnos totales del fichero .prob
        self.abierta = []  # Lista de nodos abiertos
        self.cerrada = []  # Lista de nodos cerrados
        self.tiempo_total = 0  # Para almacenar el tiempo de ejecucion

    def leerFicheroAlumnos(self):
        """Lee el fichero de entrada con la configuracion final de alumnos"""
        alumnos_sin_colocar = []  # Lista para almacenar los alumnos del fichero de entrada
        datos_alumnos_raw = open(self.path_alumnos)  # Abrimos el fichero de entrada
        datos_alumnos = eval(datos_alumnos_raw.read())  # Sacamos diccionario del fichero de entrada
        for key in datos_alumnos:
            # Separamos en una lista los valores de la clave, que contiene el id, si es conflictivo o no, o el tipo
            # de movilidad
            atributos = re.split(r'(\d+)', key)
            alumnos_sin_colocar.append(Alumno(id=int(atributos[1]),
                                              conflictivo=atributos[2][0],
                                              movilidad=atributos[2][1],
                                              asiento=datos_alumnos[key]
                                              ))
        return alumnos_sin_colocar  # Se devuelve una lista de objetos alumno

    def comprobarListaSeguro(self, lista, indice):
        """Comprueba que el indice de una lista existe"""
        """Principalmente usado para comprobar que no se coge el ultimo elemento de la lista al tratar
        de coger un elemento anterior ej: [0] -> anterior = [0-1] -> [-1]"""
        try:
            if indice < 0:
                return
            x = lista[indice]
        except Exception:
            return
        return x

    def insertarOrdenada(self, nodoNuevo):
        """Función para introducir nodo en lista abierta ordenada"""
        if len(self.abierta) == 0:  # Si la lista de nodos abiertos esta vacia
            self.abierta.append(nodoNuevo)
            return
        for i in range(len(self.abierta)):  # Se recorre la lista de nodos abiertos
            if self.abierta[i].evaluacion() >= nodoNuevo.evaluacion():  # Si un nodo de la lista tiene un f mayor
                self.abierta.insert(i, nodoNuevo)  # Se insterta delante del nodo en lista de nodos abiertos
                return
        self.abierta.append(nodoNuevo)  # Si ninguno tiene un coste menor

    def calcularHeuristica(self, alumnos_asignados, alumnos_sin_asignar):
        """Calcula la heuristica para el nodo dependiendo de la seleccionada"""

        if self.heuristica == 0:  # Fuerza bruta
            return 0

        if self.heuristica == 1:  # Peso fijo por tipo
            coste_estimado = 0
            for alumno in alumnos_sin_asignar:  # Se recorre la lista de alumnos que no estan asignados en la cola final
                if alumno.movilidad == "R":  # Si el alumno es de movilidad reducida 'XR'/'CR'
                    coste_estimado += 2  # 3 - 1 por alumno que le ayuda
                if alumno.conflictivo == "C" and alumno.movilidad != "R":  # Si el alumno es conflictivo pero no de movilidad reducida
                    if len(alumnos_asignados) == 0:
                        coste_estimado += 1  # Si el primer alumno en entrar
                    else:
                        coste_estimado += 3  # Si no, siempre suma al menos 3
                if alumno.conflictivo != "C" and alumno.movilidad != "R":  # Si es 'normal' 'XX'
                    coste_estimado += 1
            return coste_estimado  # Devolvemos un coste estimado

        if self.heuristica == 2:  # Movilidad reducida ayudados por conflictivo
            coste_estimado = 0
            n_no_conflictivos_no_mov_red = 0  # Alumnos 'normales' 'XX'
            n_mov_reducida = 0  # Alumnos que no son de mov. reducida 'XX'/'CX'
            for alumno in alumnos_sin_asignar:  # Recorremos la lista de alumnos sin asignar
                if alumno.movilidad == "R":  # Si el alumno es de movilidad reducida 'XR'/'CR'
                    coste_estimado += 2  # 3 - 1 por alumno que le ayuda
                    n_mov_reducida += 1
                if alumno.conflictivo == "C":  # Si el alumno es conflictivo
                    if alumno.movilidad != "R":  # Pero no de movilidad reducida
                        if len(alumnos_asignados) == 0:
                            coste_estimado += 1  # Si el primer alumno en entrar
                        else:
                            coste_estimado += 3  # Si no, siempre suma al menos 3
                if alumno.conflictivo != "C" and alumno.movilidad != "R":  # Si es 'normal' 'XX'
                    coste_estimado += 1
                    n_no_conflictivos_no_mov_red += 1

            # Si no hay suficientes alumnos no conflictivos para ayudar a los de mov. reducida cada alumno mov. reducida cuesta el doble
            if len(alumnos_asignados) > 0:
                primer_alumno_cola = alumnos_asignados[0]  # Si el primer alumno de la cola es no conflictivo y no mov. reducida, puede ayudar
                if primer_alumno_cola.movilidad != "R":
                    if primer_alumno_cola.conflictivo != "C":  # Si es 'normal' 'XX'
                        n_no_conflictivos_no_mov_red += 1

            coste_estimado += max(n_mov_reducida - n_no_conflictivos_no_mov_red,
                                  0) * 3  # Cada alumno mov.reducida ayudado por conflictivo suma 3
            return coste_estimado

        if self.heuristica == 3:  # Alumnos situados detrás de conflictivos tanto en asiento como en la cola
            coste_estimado = 0
            n_no_conflictivos_no_mov_red = 0
            n_mov_reducida = 0
            asientos_conflictivos = []
            for alumno in alumnos_sin_asignar:
                if alumno.movilidad == "R":
                    coste_estimado += 2  # 3 - 1 por alumno que le ayuda
                    n_mov_reducida += 1
                if alumno.conflictivo == "C":  # Vemos el coste de un alumno conflictivo para los adyacentes
                    asientos_conflictivos.append(alumno)
                    if alumno.movilidad != "R":
                        if len(self.alumnos) > 1:  # Si no es el único de la cola doblará el coste de al menos 1 adyacente + el suyo
                            coste_estimado += 3
                        else:
                            coste_estimado += 1
                if alumno.conflictivo != "C" and alumno.movilidad != "R":
                    coste_estimado += 1
                    n_no_conflictivos_no_mov_red += 1

            # Vemos cómo aumenta el coste teniendo en cuenta la cantidad de conflictivos que quedan por colocar, y que están en un asiento anterior a los alumnos ya colocados
            for alumno in alumnos_asignados:
                for conflictivo in asientos_conflictivos:
                    if alumno.asiento > conflictivo.asiento:
                        coste_estimado += 1  # Al menos dobla el coste de cada alumno detrás en la cola y en el autobús, y el mínimo coste de un alumo es 1, así que sumamos 1 para doblarlo

            return coste_estimado

    def comprobarEstadoFinal(self, nodo_actual):
        """Comprueba si el nodo expandido es el nodo final"""
        if len(nodo_actual.alumnos_asignados) == len(self.alumnos):
            # Si la lista de alumnos asignados a la cola final de un nodo,
            # tiene la misma longitud que la lista con todos los alumnos, este es un nodo final
            return True
        return False

    def calcularCoste(self, cola):
        """Se calcula el coste real en base a los alumnos que ya estan colocados en la lista final, esto se hace
        en cuatro fases distintas"""
        asientos_conflictivos = []  # Guardaremos asientos conflictivos
        costes_simples = []  # Costes de cada alumno sin tener en cuenta contexto
        costes_modificados_adyacentes = [1] * len(cola)  # coste de cada alumno teniendo en cuenta los inmediatamente adyacentes
        # Calcular los costes sin tener en cuenta las modificaciones que provocan los alumnos conflictivos y los alumnos de mov. reducida
        for alumno in cola:
            if alumno.movilidad == "R":  # Si un alumno es de movilidad reducida suma 3 al coste real 'XR'/'CR'
                costes_simples.append(3)
            else:  # Si no es de movilidad reducida 'XX'/'CX' suma 1
                costes_simples.append(1)

        # Calcular los costes que generan los alumnos conflictivos a los adyacentes a ellos en la cola
        for i in range(len(cola)):
            costes_modificados_adyacentes[i] = costes_simples[i] * costes_modificados_adyacentes[i]
            if cola[i].conflictivo == "C":  # Si el alumno es conflictivo duplica el valor del alumno anterior y posterior si existen
                alumno_anterior = self.comprobarListaSeguro(cola, i - 1)
                alumno_posterior = self.comprobarListaSeguro(cola, i + 1)
                if alumno_anterior:
                    costes_modificados_adyacentes[i - 1] = costes_modificados_adyacentes[i - 1] * 2
                if alumno_posterior and cola[i].movilidad != "R":  # Si el alumno es conflictivo y de mov. reducida no duplica al alumno que le ayda a subir 'CR'
                    costes_modificados_adyacentes[i + 1] = costes_modificados_adyacentes[i + 1] * 2

        # Bucle para calcular coste que generan los alumnos conflictivos a los que están detrás de ellos en la cola, y en el autobús
        costes_modificados_asientos = list(costes_modificados_adyacentes)  # Coste de cada alumno teniendo en cuenta si están sentados en un asiento posterior a conflictivo sentado
        for i in range(len(cola)):
            if cola[i].conflictivo == "C":
                asientos_conflictivos.append(cola[i].asiento)
            for asiento_conflictivo in asientos_conflictivos:
                if cola[i].asiento > asiento_conflictivo:
                    costes_modificados_asientos[i] = costes_modificados_asientos[i] * 2

        suma_coste = 0
        # El coste total se calcula teniendo en cuenta a los alumnos de movilidad reducida
        for i in range(len(cola)):
            if cola[i].movilidad == "R":  # Si el alumno es de movilidad reducida
                suma_coste += costes_modificados_asientos[i] * costes_modificados_asientos[i + 1]  # Coste del alumno de mov. reducida + alumno que lo ayuda
                # La operacion anterior es importante, ya que si detras de alumnos que ayuda al de mov. Red hay un conflcitivo este duplica el tiempo de ambos
                costes_modificados_asientos[i + 1] = 0  # El coste del alumno que ayuda, es el del alumno de mov. reducida
            else:
                suma_coste += costes_modificados_asientos[i]
        return suma_coste

    def crearNodoInicial(self):
        """Crea el nodo que representa la configuracion inicial del problema"""
        cola_inicial = []
        for alumno in self.alumnos:
            if alumno.movilidad != "R":
                cola_inicial.append(alumno)
                break

        if len(cola_inicial) > 0:
            inicial = Nodo(nodo_padre=None,
                           alumnos_sin_asignar=self.alumnos,
                           alumnos_asignados=[],
                           g=0,
                           h=self.calcularHeuristica(alumnos_asignados=[], alumnos_sin_asignar=self.alumnos))
            return inicial

    def expandirNodo(self, nodo_padre):
        """Calcula que almuno deberia de ser el siguiente en subir """
        sucesores = []
        cola_candidata = list(nodo_padre.alumnos_asignados)
        n_reducida = 0
        n_no_reducida = 0
        for alumno in nodo_padre.alumnos_sin_asignar:
            if alumno.movilidad == "R":
                n_reducida += 1
            else:
                n_no_reducida += 1

        if len(cola_candidata) > 0:  # si no hay suficientes alumnos para llevar a los de m
            if (n_no_reducida + (cola_candidata[0].movilidad != "R")) - n_reducida < 0:
                return sucesores  # si el numero de alumnos de movilidad reducida es superior al de movilidad no reducida, no se puede resolver

        for alumno in nodo_padre.alumnos_sin_asignar:
            if len(cola_candidata) > 0:  # mov. reducida solo si ya hay algún alumno asignado y no es de mov. reducida
                if alumno.movilidad == 'R' and cola_candidata[0].movilidad != "R":  # Comprobar restricciones alumnos movilidad reducida
                    sucesor_delante = self.generarSucesor(pos_cola=0, alumno=alumno, cola_candidata=cola_candidata,
                                                          nodo_padre=nodo_padre)
                    sucesores.append(sucesor_delante)
            if alumno.movilidad != "R":
                sucesor_delante = self.generarSucesor(pos_cola=0, alumno=alumno,
                                                      cola_candidata=cola_candidata, nodo_padre=nodo_padre)

                sucesores.append(sucesor_delante)
        return sucesores

    def generarSucesor(self, pos_cola, alumno, cola_candidata, nodo_padre):
        """Genera un nodo sucesor en base a los parametros de entrada"""
        cola_sucesor = list(cola_candidata)
        cola_sucesor.insert(pos_cola, alumno)
        alumnos_sin_asignar_candidata = list(nodo_padre.alumnos_sin_asignar)
        alumnos_sin_asignar_candidata.remove(
            alumno)  # en la lista de nodos sin asignar del sucesor eliminamos el que se ha asignado
        alumnos_asignados = list(nodo_padre.alumnos_asignados)
        nodo_sucesor = Nodo(nodo_padre=nodo_padre,
                            alumnos_sin_asignar=alumnos_sin_asignar_candidata,
                            alumnos_asignados=cola_sucesor,
                            g=(self.calcularCoste(cola_sucesor)),
                            h=self.calcularHeuristica(alumnos_sin_asignar=alumnos_sin_asignar_candidata,
                                                      alumnos_asignados=alumnos_asignados))
        return nodo_sucesor

    def sucesorEnAbierta(self, nodo):
        """Comprueba si un nodo esta en la lista de nodos abiertos"""
        try:
            i_nodo_duplicado = self.abierta.index(nodo)
        except ValueError:
            return None
        return self.abierta[i_nodo_duplicado]

    def crearFicheroSalida(self, nodo_final):
        """Se encarga de crear los ficheros de salida"""
        """Fichero resultados"""
        fichero_resultado = open(self.nombre_fichero_alumnos + '-' + str(self.heuristica) + ".output", "w")
        diccionario_inicial = {}  # Cola inicial
        diccionario_final = {}  # Cola optima
        if len(nodo_final.alumnos_sin_asignar) == 0:
            for i in range(len(self.alumnos)):  # Guardar en orden ambas colas, ambas deben tener la misma longitud
                diccionario_inicial[str(self.alumnos[i].id) + self.alumnos[i].conflictivo + self.alumnos[i].movilidad] = \
                    self.alumnos[i].asiento
                diccionario_final[str(nodo_final.alumnos_asignados[i].id) + nodo_final.alumnos_asignados[i].conflictivo +
                                  nodo_final.alumnos_asignados[i].movilidad] = nodo_final.alumnos_asignados[i].asiento
            resultados = f"INICIAL: {diccionario_inicial} \nFINAL: {diccionario_final}"  # Formato del archivo
            fichero_resultado.write(resultados)  # Escritura al archivo
            fichero_resultado.close()  # Cierre del archivo
        """Fichero estadisticas"""
        fichero_estadistica = open(self.nombre_fichero_alumnos + '-' + str(self.heuristica) + ".stat", "w")
        estadistica = f"Tiempo total: {self.tiempo_total}s\nCoste total: {nodo_final.g}\nLongitud del plan: {len(self.alumnos)}\nNodos expandidos: {len(self.cerrada)}"
        fichero_estadistica.write(estadistica)
        fichero_estadistica.close()

    def busquedaAStar(self):
        """Metodo principal donde se ejecuta el algoritmo"""
        tiempo_inicial = time.time()  # Se guarda al hora actual como hora de inicio
        nodo_inicial = self.crearNodoInicial()  # Se crea el nodo inicial
        if nodo_inicial is None:  # Si no se ha podido crear ningun nodo inical
            tiempo_final = time.time()
            self.tiempo_total = tiempo_final - tiempo_inicial
            exit(f"No existe solución factible\nTiempo de ejecucion: {self.tiempo_total}s")
        self.abierta.append(nodo_inicial)
        while len(self.abierta) > 0:
            nodo_actual = self.abierta.pop(0)

            if self.comprobarEstadoFinal(nodo_actual):
                """FINAL DEL ALGORITMO CON SOLUCION"""
                tiempo_final = time.time()
                self.tiempo_total = tiempo_final - tiempo_inicial
                self.crearFicheroSalida(nodo_actual)
                exit("Solución Encontrada")

            # si no hemos encontrado el nodo final
            self.cerrada.append(nodo_actual)
            sucesores = self.expandirNodo(nodo_actual)

            for sucesor in sucesores:

                if sucesor in self.cerrada:
                    continue  # como es monótona sabemos que el nodo en cerrada tiene menor coste

                sucesorEnAbierta = self.sucesorEnAbierta(sucesor)
                if sucesorEnAbierta is None:  # si no existe el sucesor en abierta lo metemos en la lista
                    self.insertarOrdenada(sucesor)
                else:  # si ya existe el nodo en abierta comprobamos si el actual tiene mejor coste
                    if sucesorEnAbierta.evaluacion() > sucesor.evaluacion():  # Si el nodo en abierta tiene peor coste
                        self.abierta.remove(sucesorEnAbierta)
                        self.insertarOrdenada(sucesor)
                    # Si el nuevo nodo es igual o peor se ignora
        tiempo_final = time.time()
        self.tiempo_total = tiempo_final - tiempo_inicial
        self.crearFicheroSalida(nodo_actual)
        print("No se encuentra solución")
        return


if __name__ == "__main__":
    """Llamada al programa"""
    if len(sys.argv) < 3:
        exit("Faltan argumentos, formato incorrecto.")

    path_directorio = sys.argv[1]
    fichero_alumnos = sys.argv[2]
    heuristica = int(sys.argv[3])

    problem = AStar(path_directorio, fichero_alumnos, heuristica)
    problem.busquedaAStar()

