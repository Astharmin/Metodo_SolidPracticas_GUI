import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import tkinter.font as tkfont


@dataclass
class TareaData:
    """DTO para transferencia de datos de tareas"""
    descripcion: str
    prioridad: int


class Nodo(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass


class Tarea(Nodo):
    def __init__(self, descripcion: str, prioridad: int):
        self.descripcion = descripcion
        self.prioridad = prioridad
        self.siguiente: Optional[Tarea] = None

    def __str__(self):
        return f"[{self.prioridad}] {self.descripcion}"


class OperacionesLista(ABC):
    @abstractmethod
    def agregar(self, tarea_data: TareaData) -> None:
        pass

    @abstractmethod
    def eliminar(self, descripcion: str) -> bool:
        pass

    @abstractmethod
    def obtener_todas(self) -> list[Tarea]:
        pass

    @abstractmethod
    def buscar(self, descripcion: str) -> Optional[Tarea]:
        pass


class IteradorTareas:
    def __init__(self, cabeza: Optional[Tarea]):
        self.actual = cabeza

    def __iter__(self):
        return self

    def __next__(self) -> Tarea:
        if not self.actual:
            raise StopIteration
        tarea = self.actual
        self.actual = self.actual.siguiente
        return tarea


class FiltroTareas(ABC):
    @abstractmethod
    def filtrar(self, tarea: Tarea) -> bool:
        pass


class FiltroPorPrioridad(FiltroTareas):
    def __init__(self, prioridad: int):
        self.prioridad = prioridad

    def filtrar(self, tarea: Tarea) -> bool:
        return tarea.prioridad == self.prioridad


class FiltroPorTexto(FiltroTareas):
    def __init__(self, texto: str):
        self.texto = texto.lower()

    def filtrar(self, tarea: Tarea) -> bool:
        return self.texto in tarea.descripcion.lower()


class ListaTareas(OperacionesLista):
    def __init__(self):
        self.cabeza: Optional[Tarea] = None

    def agregar(self, tarea_data: TareaData) -> None:
        nueva_tarea = Tarea(tarea_data.descripcion, tarea_data.prioridad)
        nueva_tarea.siguiente = self.cabeza
        self.cabeza = nueva_tarea

    def agregar_al_final(self, tarea_data: TareaData) -> None:
        nueva_tarea = Tarea(tarea_data.descripcion, tarea_data.prioridad)

        if not self.cabeza:
            self.cabeza = nueva_tarea
            return

        actual = self.cabeza
        while actual.siguiente:
            actual = actual.siguiente
        actual.siguiente = nueva_tarea

    def eliminar(self, descripcion: str) -> bool:
        actual = self.cabeza
        anterior = None

        while actual:
            if actual.descripcion == descripcion:
                if anterior:
                    anterior.siguiente = actual.siguiente
                else:
                    self.cabeza = actual.siguiente
                return True
            anterior = actual
            actual = actual.siguiente

        return False

    def buscar(self, descripcion: str) -> Optional[Tarea]:
        for tarea in self.obtener_iterador():
            if tarea.descripcion.lower() == descripcion.lower():
                return tarea
        return None

    def obtener_iterador(self) -> IteradorTareas:
        return IteradorTareas(self.cabeza)

    def obtener_todas(self) -> list[Tarea]:
        return list(self.obtener_iterador())

    def aplicar_filtro(self, filtro: FiltroTareas) -> list[Tarea]:
        return [tarea for tarea in self.obtener_iterador() if filtro.filtrar(tarea)]

    def contar(self) -> int:
        return sum(1 for _ in self.obtener_iterador())


class PresentadorTareas(ABC):
    @abstractmethod
    def mostrar_tarea_agregada(self, tarea: Tarea) -> None:
        pass

    @abstractmethod
    def mostrar_tarea_eliminada(self, tarea: Tarea) -> None:
        pass

    @abstractmethod
    def mostrar_tarea_encontrada(self, tarea: Tarea, posicion: int) -> None:
        pass

    @abstractmethod
    def mostrar_tarea_no_encontrada(self, descripcion: str) -> None:
        pass

    @abstractmethod
    def mostrar_error(self, mensaje: str) -> None:
        pass

    @abstractmethod
    def actualizar_lista_tareas(self, tareas: list[Tarea]) -> None:
        pass


class PresentadorTareasGUI(PresentadorTareas):
    def __init__(self, lista_widget, status_var):
        self.lista_widget = lista_widget
        self.status_var = status_var

    def mostrar_tarea_agregada(self, tarea: Tarea) -> None:
        self.status_var.set(f"✓ Tarea agregada: {tarea.descripcion}")

    def mostrar_tarea_eliminada(self, tarea: Tarea) -> None:
        self.status_var.set(f"🗑️ Tarea eliminada: {tarea.descripcion}")

    def mostrar_tarea_encontrada(self, tarea: Tarea, posicion: int) -> None:
        self.status_var.set(f"🔍 Tarea encontrada en posición {posicion}: {tarea.descripcion}")

    def mostrar_tarea_no_encontrada(self, descripcion: str) -> None:
        self.status_var.set(f"❌ Tarea '{descripcion}' no encontrada")

    def mostrar_error(self, mensaje: str) -> None:
        messagebox.showerror("Error", mensaje)
        self.status_var.set(f"⚠️ {mensaje}")

    def actualizar_lista_tareas(self, tareas: list[Tarea]) -> None:
        self.lista_widget.delete(*self.lista_widget.get_children())

        for tarea in tareas:
            prioridad_texto = self._obtener_texto_prioridad(tarea.prioridad)
            prioridad_color = self._obtener_color_prioridad(tarea.prioridad)

            self.lista_widget.insert("", "end",
                                     values=(tarea.descripcion, prioridad_texto),
                                     tags=(prioridad_color,))

    def _obtener_texto_prioridad(self, prioridad: int) -> str:
        prioridades = {1: "Alta", 2: "Media", 3: "Baja"}
        return prioridades.get(prioridad, f"Prioridad {prioridad}")

    def _obtener_color_prioridad(self, prioridad: int) -> str:
        colores = {1: "alta", 2: "media", 3: "baja"}
        return colores.get(prioridad, "baja")


class ServicioTareas:
    def __init__(self, lista_tareas: ListaTareas, presentador: PresentadorTareas):
        self.lista_tareas = lista_tareas
        self.presentador = presentador

    def agregar_tarea(self, descripcion: str, prioridad: int, al_final: bool = False) -> bool:
        if not descripcion.strip():
            self.presentador.mostrar_error("La descripción no puede estar vacía")
            return False

        tarea_data = TareaData(descripcion.strip(), prioridad)

        if al_final:
            self.lista_tareas.agregar_al_final(tarea_data)
        else:
            self.lista_tareas.agregar(tarea_data)

        tarea = self.lista_tareas.buscar(descripcion)
        if tarea:
            self.presentador.mostrar_tarea_agregada(tarea)
            self._actualizar_vista()
            return True
        return False

    def eliminar_tarea(self, descripcion: str) -> bool:
        tarea = self.lista_tareas.buscar(descripcion)
        if tarea and self.lista_tareas.eliminar(descripcion):
            self.presentador.mostrar_tarea_eliminada(tarea)
            self._actualizar_vista()
            return True
        else:
            self.presentador.mostrar_tarea_no_encontrada(descripcion)
            return False

    def buscar_tarea(self, descripcion: str) -> None:
        tarea = self.lista_tareas.buscar(descripcion)
        if tarea:
            posicion = self._obtener_posicion(tarea)
            self.presentador.mostrar_tarea_encontrada(tarea, posicion)
        else:
            self.presentador.mostrar_tarea_no_encontrada(descripcion)

    def filtrar_tareas_por_prioridad(self, prioridad: int) -> None:
        filtro = FiltroPorPrioridad(prioridad)
        tareas_filtradas = self.lista_tareas.aplicar_filtro(filtro)
        self.presentador.actualizar_lista_tareas(tareas_filtradas)
        self.presentador.mostrar_tarea_agregada(Tarea(f"Filtrado por prioridad {prioridad}", prioridad))

    def filtrar_tareas_por_texto(self, texto: str) -> None:
        filtro = FiltroPorTexto(texto)
        tareas_filtradas = self.lista_tareas.aplicar_filtro(filtro)
        self.presentador.actualizar_lista_tareas(tareas_filtradas)

    def mostrar_todas_tareas(self) -> None:
        tareas = self.lista_tareas.obtener_todas()
        self.presentador.actualizar_lista_tareas(tareas)

    def obtener_estadisticas(self) -> dict:
        total = self.lista_tareas.contar()
        tareas = self.lista_tareas.obtener_todas()
        prioridades = {1: 0, 2: 0, 3: 0}

        for tarea in tareas:
            prioridades[tarea.prioridad] = prioridades.get(tarea.prioridad, 0) + 1

        return {
            "total": total,
            "prioridades": prioridades
        }

    def _obtener_posicion(self, tarea_buscada: Tarea) -> int:
        for i, tarea in enumerate(self.lista_tareas.obtener_iterador(), 1):
            if tarea is tarea_buscada:
                return i
        return -1

    def _actualizar_vista(self) -> None:
        self.mostrar_todas_tareas()


class AplicacionTareas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Tareas - SOLID")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')

        # Configurar estilos
        self._configurar_estilos()

        # Inicializar componentes
        self.lista_tareas = ListaTareas()
        self._crear_interfaz()

        # Inyectar dependencias
        presentador = PresentadorTareasGUI(self.treeview, self.status_var)
        self.servicio = ServicioTareas(self.lista_tareas, presentador)

        # Cargar datos de ejemplo
        self._cargar_datos_ejemplo()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Configurar colores para prioridades
        style.configure("alta.Treeview", background='#ffebee')
        style.configure("media.Treeview", background='#fff3e0')
        style.configure("baja.Treeview", background='#e8f5e8')

    def _crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Título
        titulo = ttk.Label(main_frame, text="🎯 Gestor de Tareas",
                           font=tkfont.Font(family="Arial", size=16, weight="bold"))
        titulo.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Frame de entrada
        entrada_frame = ttk.LabelFrame(main_frame, text="Nueva Tarea", padding="10")
        entrada_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        entrada_frame.columnconfigure(1, weight=1)

        ttk.Label(entrada_frame, text="Descripción:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.descripcion_var = tk.StringVar()
        self.entry_descripcion = ttk.Entry(entrada_frame, textvariable=self.descripcion_var, width=40)
        self.entry_descripcion.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.entry_descripcion.bind('<Return>', lambda e: self.agregar_tarea())

        ttk.Label(entrada_frame, text="Prioridad:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.prioridad_var = tk.IntVar(value=2)
        ttk.Combobox(entrada_frame, textvariable=self.prioridad_var,
                     values=[1, 2, 3], state="readonly", width=10).grid(row=0, column=3, padx=(0, 10))

        ttk.Button(entrada_frame, text="Agregar Tarea",
                   command=self.agregar_tarea, style="Accent.TButton").grid(row=0, column=4)

        # Frame de búsqueda y filtros
        filtros_frame = ttk.LabelFrame(main_frame, text="Búsqueda y Filtros", padding="10")
        filtros_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        filtros_frame.columnconfigure(1, weight=1)

        ttk.Label(filtros_frame, text="Buscar:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.busqueda_var = tk.StringVar()
        self.entry_busqueda = ttk.Entry(filtros_frame, textvariable=self.busqueda_var, width=30)
        self.entry_busqueda.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.entry_busqueda.bind('<KeyRelease>', self.filtrar_por_texto)

        ttk.Button(filtros_frame, text="Buscar",
                   command=self.buscar_tarea).grid(row=0, column=2, padx=(0, 10))

        ttk.Label(filtros_frame, text="Filtrar por prioridad:").grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.filtro_prioridad_var = tk.StringVar(value="Todas")
        prioridad_combo = ttk.Combobox(filtros_frame, textvariable=self.filtro_prioridad_var,
                                       values=["Todas", "Alta (1)", "Media (2)", "Baja (3)"],
                                       state="readonly", width=12)
        prioridad_combo.grid(row=0, column=4, padx=(0, 10))
        prioridad_combo.bind('<<ComboboxSelected>>', self.filtrar_por_prioridad)

        # Lista de tareas
        lista_frame = ttk.LabelFrame(main_frame, text="Tareas Pendientes", padding="10")
        lista_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        lista_frame.columnconfigure(0, weight=1)
        lista_frame.rowconfigure(0, weight=1)

        # Treeview para mostrar tareas
        columns = ("Descripción", "Prioridad")
        self.treeview = ttk.Treeview(lista_frame, columns=columns, show="headings", height=12)

        # Configurar columnas
        self.treeview.heading("Descripción", text="Descripción")
        self.treeview.heading("Prioridad", text="Prioridad")
        self.treeview.column("Descripción", width=400)
        self.treeview.column("Prioridad", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=scrollbar.set)

        self.treeview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Configurar tags para colores de prioridad
        self.treeview.tag_configure('alta', background='#ffebee')
        self.treeview.tag_configure('media', background='#fff3e0')
        self.treeview.tag_configure('baja', background='#e8f5e8')

        # Frame de acciones
        acciones_frame = ttk.Frame(main_frame)
        acciones_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(acciones_frame, text="Eliminar Seleccionada",
                   command=self.eliminar_tarea_seleccionada, style="Danger.TButton").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(acciones_frame, text="Mostrar Todas",
                   command=self.mostrar_todas).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(acciones_frame, text="Estadísticas",
                   command=self.mostrar_estadisticas).pack(side=tk.LEFT)

        # Barra de estado
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.status_var = tk.StringVar(value="Listo")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                 relief=tk.SUNKEN, style="Status.TLabel")
        status_label.pack(fill=tk.X, ipady=2)

    def _cargar_datos_ejemplo(self):
        tareas_ejemplo = [
            ("Estudiar para el examen", 1),
            ("Hacer ejercicio", 2),
            ("Comprar víveres", 2),
            ("Llamar al médico", 1),
            ("Leer libro", 3)
        ]

        for descripcion, prioridad in tareas_ejemplo:
            self.servicio.agregar_tarea(descripcion, prioridad)

    def agregar_tarea(self):
        descripcion = self.descripcion_var.get()
        prioridad = self.prioridad_var.get()

        if self.servicio.agregar_tarea(descripcion, prioridad):
            self.descripcion_var.set("")
            self.entry_descripcion.focus()

    def eliminar_tarea_seleccionada(self):
        seleccion = self.treeview.selection()
        if seleccion:
            item = seleccion[0]
            descripcion = self.treeview.item(item, 'values')[0]
            self.servicio.eliminar_tarea(descripcion)

    def buscar_tarea(self):
        descripcion = self.busqueda_var.get()
        if descripcion.strip():
            self.servicio.buscar_tarea(descripcion)

    def filtrar_por_prioridad(self, event=None):
        filtro = self.filtro_prioridad_var.get()
        if filtro == "Alta (1)":
            self.servicio.filtrar_tareas_por_prioridad(1)
        elif filtro == "Media (2)":
            self.servicio.filtrar_tareas_por_prioridad(2)
        elif filtro == "Baja (3)":
            self.servicio.filtrar_tareas_por_prioridad(3)
        else:
            self.servicio.mostrar_todas_tareas()

    def filtrar_por_texto(self, event=None):
        texto = self.busqueda_var.get()
        if texto.strip():
            self.servicio.filtrar_tareas_por_texto(texto)
        else:
            self.servicio.mostrar_todas_tareas()

    def mostrar_todas(self):
        self.servicio.mostrar_todas_tareas()
        self.filtro_prioridad_var.set("Todas")
        self.busqueda_var.set("")
        self.status_var.set("Mostrando todas las tareas")

    def mostrar_estadisticas(self):
        stats = self.servicio.obtener_estadisticas()
        mensaje = (f"📊 Estadísticas de Tareas:\n\n"
                   f"Total de tareas: {stats['total']}\n"
                   f"Alta prioridad: {stats['prioridades'][1]}\n"
                   f"Media prioridad: {stats['prioridades'][2]}\n"
                   f"Baja prioridad: {stats['prioridades'][3]}")

        messagebox.showinfo("Estadísticas", mensaje)


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionTareas(root)
    root.mainloop()