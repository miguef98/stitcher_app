import tkinter as tk
from tkinter import filedialog
import threading
from stitcher import crearPanorama
from PIL import ImageTk, Image
from time import sleep
import argparse

class TextoEntry(tk.Entry):
    def __init__(self, textoInicial, parent, *args, **kwargs):
        tk.Entry.__init__(self, parent, *args, **kwargs)

        self.textoInicial = textoInicial
        self.insert(0, self.textoInicial)
        self.bind("<FocusIn>", self.handle_focus_in)

    def handle_focus_in( self,_ ):
        self.delete(0, tk.END)
        self.config(fg='black')

class MenuIngresoGrilla(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.grid(rows=1, columns=3)
        self.parent = parent

        self.filasEntry = TextoEntry("Ingrese filas", self ,foreground="grey")
        self.filasEntry.grid(row=1, column=1)

        self.columnasEntry= TextoEntry("Ingrese columnas", self, foreground="grey")
        self.columnasEntry.grid(row=1, column=2)

        self.botonIngreso = tk.Button( self, text="Entrar", command=lambda: self.parent.crearGrilla( self, self.filasEntry.get(), self.columnasEntry.get()))
        self.botonIngreso.grid(row=1, column=3)

class MenuIngresoImagenes(tk.Frame):
    def __init__(self, parent, grilla, ancho, alto, descriptor, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.grilla = grilla
        self.grid(rows=self.grilla[0] + 1, columns=self.grilla[1])
        self.parent = parent
        self.descriptor = descriptor

        self.pathImagenes = [ None for _ in range( self.grilla[0] * self.grilla[1] ) ]

        self.frames = [ FrameImagen(self, i, width= int(ancho/self.grilla[0]), height=int(alto/self.grilla[1]), highlightbackground="grey", highlightthickness=1) for i in range(self.grilla[0] * self.grilla[1]) ]
        for idx, frame in enumerate( self.frames):
            frame.grid( row = idx // self.grilla[1], column = idx % self.grilla[1])
            frame.grid_propagate(False)

        self.botonAceptar = tk.Button( self, text="Pegar imagenes", command=self.realizarPegado, state='disabled' )
        self.botonAceptar.grid( row= self.grilla[0], column=self.grilla[1] - 1)

    def realizarPegado( self ):
        self.botonAceptar['state'] = 'disabled'
        for frame in self.frames:
            frame.desabilitarBoton()

        def threadPanorama( valorRetorno, *args, **kwargs ):
            try:
                crearPanorama(*args, **kwargs)
                valorRetorno[0] = 0
            except Exception as e:
                valorRetorno[0] = int( str(e)[0:2] ) if str(e)[0:2].isnumeric() else -1
            
            return

        def animacionEspera( parent, tid, valorRetorno ):
            texto = "Realizando pegado\n(puede demorar varios minutos)\n"
            label = tk.Label( parent, text=texto, background='#888', padx=30, pady=20 )
            label.grid(row= 0, column = 0, rowspan=parent.grilla[0], columnspan=parent.grilla[1])

            contador = 0
            while tid.is_alive():
                if contador == 3:
                    texto = "Realizando pegado\n(puede demorar varios minutos)\n"
                    contador = 0
                else:
                    texto += " ."
                
                label.config(text=texto)    
                sleep(1)
                contador += 1

            label.destroy()

            texto = "El pegado fue realizado con exito"
            if valorRetorno[0] != 0:
                texto = "Hubo un error al realizar el pegado (codigo " + str(valorRetorno[0]) + ")."

            label = tk.Label( parent, text=texto, background='#BBB', padx=30, pady=20 )
            label.grid(row= 0, column = 0, rowspan=parent.grilla[0], columnspan=parent.grilla[1])

        resultadoPegado = [1]
        threadStitch = threading.Thread( target=threadPanorama, args=(resultadoPegado,  self.grilla, self.pathImagenes, self.descriptor) )
        threadAnimacion = threading.Thread( target=animacionEspera, args=(self, threadStitch, resultadoPegado) )

        threadStitch.start()
        threadAnimacion.start()
        
    def cargarImagen( self, frameIndex, path ):
        self.pathImagenes[ frameIndex ] = path

        if all([ not pathI is None for pathI in self.pathImagenes]):
            self.botonAceptar["state"] = 'normal'


class FrameImagen(tk.Frame):
    def __init__(self, parent, index, *args, **kwargs ):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.grid( rows=1, columns=1)
        self.parent = parent
        self.grid_propagate(False)
        self.imagen = None
        self.labelImagen = tk.Label(self)
        self.labelImagen.grid(row=0, column=0)
        self.index = index

        def seleccionarArchivo( frame ):
            filetypes = (
                ('Image files', ('*.bmp', '*.dib', '*.jpeg', '*.jpg', '*.jpe', '*.jp2', '*.png', '*.webp', '*.pbm', '*.pgm', '*.ppm', '*.pxm', '*.pnm', '*.pfm', '*.sr', '*.ras', '*.tiff', '*.tif', '*.exr', '*.hdr', '*.pic') ),
                ('All files', '*.*')
            )

            try:
                frame.agregarImagen( filedialog.askopenfilename( title='Open a file', initialdir='~/', filetypes=filetypes) )
            except:
                return

        self.botonAbrirImagen = tk.Button( self, text='Abrir imagen',command=lambda: seleccionarArchivo(self) )
        self.botonAbrirImagen.grid(row=0, column=0)
        self.botonAbrirImagen.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def agregarImagen( self, pathImagen ):
        if self.imagen is None:
            self.configurarBotonInvisible()

        nuevaImagen = Image.open(pathImagen)
        nuevaImagen.thumbnail((self.winfo_width(), self.winfo_height()), Image.Resampling.LANCZOS)
        self.imagen = ImageTk.PhotoImage( nuevaImagen )
        self.labelImagen.configure(image = self.imagen)
        self.labelImagen.image = self.imagen
        self.labelImagen.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.onLeave( "b")
        self.parent.cargarImagen( self.index, pathImagen )

    def configurarBotonInvisible( self ):
        self.bind('<Enter>', func=self.onEnter)
        self.bind('<Leave>', func=self.onLeave)

    def onEnter( self, e ):
        self.botonAbrirImagen.grid(row=0, column=0)
        self.botonAbrirImagen.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def onLeave(self, e):
        self.botonAbrirImagen.place_forget()

    def desabilitarBoton( self ):
        self.botonAbrirImagen['state'] = 'disabled'

class App(tk.Tk):
    def __init__( self, width, height, descriptor ):
        super().__init__()
        self.title("Stitcher")
        self.width = width
        self.height = height
        self.descriptor = descriptor

    def crearGrilla( self, frame, w, h ):
        if w.isnumeric() and h.isnumeric():
            frame.grid_forget()
            frame.destroy()

            MenuIngresoImagenes(self, (int(w), int(h)), self.width, self.height, self.descriptor)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-wd", "--width", help="setear ancho ventana", default=640, type=int)
    parser.add_argument("-hg", "--height", help="setear alto ventana", default=480, type=int)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--SIFT", help="utilizar SIFT como descriptor", action="store_true")
    group.add_argument("--ORB", help="utilizar ORB como descriptor", action="store_true")
    args = parser.parse_args()

    root = App( args.width, args.height, {'SIFT': args.SIFT, 'SURF': not (args.SIFT or args.ORB), 'ORB': args.ORB} )
    MenuIngresoGrilla(root, padx=10, pady=10)
    root.mainloop()