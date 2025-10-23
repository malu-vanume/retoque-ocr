import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import os
from pathlib import Path
import threading

class WatermarkRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Removedor de Marcas de Agua - IA Avanzado")
        self.root.geometry("900x650")
        self.root.configure(bg='#f0f4f8')
        
        self.files = []
        self.output_pdf = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Título
        title_frame = tk.Frame(self.root, bg='#f0f4f8')
        title_frame.pack(pady=20)
        
        tk.Label(title_frame, text="Removedor de Marcas de Agua Avanzado", 
                font=('Helvetica', 24, 'bold'), bg='#f0f4f8', fg='#1e40af').pack()
        tk.Label(title_frame, text="Remueve líneas azules, sellos, firmas y marcas de agua automáticamente",
                font=('Helvetica', 11), bg='#f0f4f8', fg='#64748b').pack()
        
        # Área de drop
        drop_frame = tk.Frame(self.root, bg='#e0e7ff', relief=tk.RIDGE, bd=3)
        drop_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.drop_files)
        
        tk.Label(drop_frame, text="📁 Arrastra tus archivos aquí", 
                font=('Helvetica', 16, 'bold'), bg='#e0e7ff', fg='#4f46e5').pack(pady=15)
        tk.Label(drop_frame, text="Formatos soportados: JPG, PNG, BMP, JPEG, PDF",
                font=('Helvetica', 10), bg='#e0e7ff', fg='#6366f1').pack()
        
        # Botón seleccionar
        btn_select = tk.Button(drop_frame, text="Seleccionar Archivos", 
                              command=self.select_files,
                              bg='#4f46e5', fg='white', font=('Helvetica', 12, 'bold'),
                              padx=20, pady=10, relief=tk.FLAT, cursor='hand2')
        btn_select.pack(pady=15)
        
        # Lista de archivos
        self.files_listbox = tk.Listbox(drop_frame, height=6, bg='white', 
                                        font=('Helvetica', 10), relief=tk.FLAT)
        self.files_listbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Frame de opciones
        options_frame = tk.Frame(self.root, bg='#f0f4f8')
        options_frame.pack(pady=10)
        
        tk.Label(options_frame, text="Remover:", font=('Helvetica', 10, 'bold'),
                bg='#f0f4f8').pack(side=tk.LEFT, padx=10)
        
        self.remove_blue_lines = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Líneas azules", variable=self.remove_blue_lines,
                      bg='#f0f4f8', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=5)
        
        self.remove_seals = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Sellos", variable=self.remove_seals,
                      bg='#f0f4f8', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=5)
        
        self.remove_signatures = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Firmas", variable=self.remove_signatures,
                      bg='#f0f4f8', font=('Helvetica', 10)).pack(side=tk.LEFT, padx=5)
        
        # Botones de acción
        action_frame = tk.Frame(self.root, bg='#f0f4f8')
        action_frame.pack(pady=10)
        
        self.btn_process = tk.Button(action_frame, text="🔄 Limpiar Documento", 
                                     command=self.process_files,
                                     bg='#10b981', fg='white', font=('Helvetica', 12, 'bold'),
                                     padx=30, pady=12, relief=tk.FLAT, cursor='hand2',
                                     state=tk.DISABLED)
        self.btn_process.pack(side=tk.LEFT, padx=10)
        
        self.btn_download = tk.Button(action_frame, text="⬇️ Descargar PDF Limpio", 
                                      command=self.download_pdf,
                                      bg='#0ea5e9', fg='white', font=('Helvetica', 12, 'bold'),
                                      padx=30, pady=12, relief=tk.FLAT, cursor='hand2',
                                      state=tk.DISABLED)
        self.btn_download.pack(side=tk.LEFT, padx=10)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(pady=10, padx=40, fill=tk.X)
        
        # Status
        self.status_label = tk.Label(self.root, text="Esperando archivos...", 
                                     font=('Helvetica', 10), bg='#f0f4f8', fg='#64748b')
        self.status_label.pack(pady=5)
        
    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos",
            filetypes=[("Imágenes y PDFs", "*.jpg *.jpeg *.png *.bmp *.pdf")]
        )
        self.add_files(files)
        
    def add_files(self, files):
        for file in files:
            if file not in self.files:
                self.files.append(file)
                filename = os.path.basename(file)
                self.files_listbox.insert(tk.END, filename)
        
        if self.files:
            self.btn_process.config(state=tk.NORMAL)
            self.status_label.config(text=f"{len(self.files)} archivo(s) cargado(s)")
    
    def remove_blue_lines_from_image(self, img):
        """Detectar y remover líneas azules (horizontales principalmente)"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Rango para detectar líneas azules (ajustado para varios tonos de azul)
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])
        
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Morfología para conectar líneas
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel_horizontal)
        
        # Dilatar para cubrir toda la línea
        kernel_dilate = np.ones((3, 3), np.uint8)
        mask_blue = cv2.dilate(mask_blue, kernel_dilate, iterations=2)
        
        # Inpainting para rellenar
        result = cv2.inpaint(img, mask_blue, 7, cv2.INPAINT_TELEA)
        
        return result
    
    def remove_circular_seals(self, img):
        """Detectar y remover sellos circulares o semicirculares"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detectar bordes
        edges = cv2.Canny(gray, 50, 150)
        
        # Detectar círculos (sellos circulares)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                                   param1=50, param2=30, minRadius=20, maxRadius=150)
        
        mask = np.zeros(gray.shape, dtype=np.uint8)
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                center = (circle[0], circle[1])
                radius = circle[2]
                # Dibujar círculo relleno en la máscara
                cv2.circle(mask, center, radius + 10, 255, -1)
        
        # Detectar también áreas con mucho contenido rojo/azul (sellos comunes)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Rojo (sellos rojos)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # Combinar con la máscara de círculos
        mask = cv2.bitwise_or(mask, mask_red)
        
        # Morfología para limpiar
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        # Inpainting
        result = cv2.inpaint(img, mask, 7, cv2.INPAINT_TELEA)
        
        return result
    
    def remove_handwritten_signatures(self, img):
        """Detectar y remover firmas manuscritas"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Umbral adaptativo para detectar texto/trazos
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        # Morfología para conectar trazos de firma
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        mask = np.zeros(gray.shape, dtype=np.uint8)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            
            # Filtrar características típicas de firmas:
            # - Área media (no muy pequeña ni muy grande)
            # - Relación de aspecto horizontal (firmas son más anchas)
            # - No es texto regular (más irregular)
            if 500 < area < 15000 and 1.5 < aspect_ratio < 8:
                # Verificar densidad de píxeles (firmas tienen densidad media)
                roi = thresh[y:y+h, x:x+w]
                density = np.sum(roi > 0) / (w * h) if (w * h) > 0 else 0
                
                if 0.05 < density < 0.4:  # Firmas tienen densidad característica
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    # Expandir un poco la máscara
                    cv2.rectangle(mask, (x-5, y-5), (x+w+5, y+h+5), 255, -1)
        
        # Dilatar para cubrir toda la firma
        kernel_dilate = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel_dilate, iterations=2)
        
        # Inpainting
        result = cv2.inpaint(img, mask, 7, cv2.INPAINT_TELEA)
        
        return result
    
    def clean_document(self, image_path):
        """Limpieza completa del documento según opciones seleccionadas"""
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        result = img.copy()
        
        # Aplicar filtros según selección del usuario
        if self.remove_blue_lines.get():
            result = self.remove_blue_lines_from_image(result)
        
        if self.remove_seals.get():
            result = self.remove_circular_seals(result)
        
        if self.remove_signatures.get():
            result = self.remove_handwritten_signatures(result)
        
        # Mejora final: suavizar y mejorar contraste
        result = cv2.bilateralFilter(result, 5, 75, 75)
        
        return result
    
    def process_pdf(self, pdf_path):
        """Procesar PDF: extraer páginas, limpiar y reconstruir"""
        doc = fitz.open(pdf_path)
        processed_images = []
        temp_dir = os.path.join(os.path.expanduser("~"), "temp_watermark")
        os.makedirs(temp_dir, exist_ok=True)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Alta resolución para mejor detección
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            
            # Guardar temporalmente
            temp_img_path = os.path.join(temp_dir, f"page_{page_num}.png")
            pix.save(temp_img_path)
            
            # Limpiar imagen
            cleaned_img = self.clean_document(temp_img_path)
            
            if cleaned_img is not None:
                processed_images.append(cleaned_img)
            
            # Limpiar archivo temporal
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
        
        doc.close()
        
        # Limpiar directorio temporal
        try:
            os.rmdir(temp_dir)
        except:
            pass
            
        return processed_images
    
    def create_pdf_from_images(self, images, output_path):
        """Crear PDF desde imágenes procesadas"""
        if not images:
            return False
        
        # Convertir imágenes a PIL
        pil_images = []
        for img in images:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            pil_images.append(pil_img)
        
        # Guardar como PDF con alta calidad
        if pil_images:
            pil_images[0].save(output_path, "PDF", resolution=300.0, 
                             save_all=True, append_images=pil_images[1:] if len(pil_images) > 1 else [])
            return True
        
        return False
    
    def process_files_thread(self):
        """Procesar archivos en thread separado"""
        self.progress.start()
        self.status_label.config(text="🔄 Limpiando documentos con IA...")
        
        processed_images = []
        
        try:
            for file_path in self.files:
                ext = Path(file_path).suffix.lower()
                
                if ext == '.pdf':
                    # Procesar PDF
                    images = self.process_pdf(file_path)
                    processed_images.extend(images)
                else:
                    # Procesar imagen
                    cleaned_img = self.clean_document(file_path)
                    if cleaned_img is not None:
                        processed_images.append(cleaned_img)
            
            # Crear PDF de salida
            output_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            self.output_pdf = os.path.join(output_dir, "documento_limpio.pdf")
            
            if self.create_pdf_from_images(processed_images, self.output_pdf):
                self.progress.stop()
                self.status_label.config(text="✅ ¡Documento limpio creado exitosamente!")
                self.btn_download.config(state=tk.NORMAL)
                self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                    "¡Documento limpiado exitosamente!\n\nSe removieron:\n" +
                    ("✓ Líneas azules\n" if self.remove_blue_lines.get() else "") +
                    ("✓ Sellos\n" if self.remove_seals.get() else "") +
                    ("✓ Firmas manuscritas\n" if self.remove_signatures.get() else "")))
            else:
                raise Exception("Error al crear PDF")
                
        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="❌ Error en el procesamiento")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
    
    def process_files(self):
        """Iniciar procesamiento en thread"""
        if not self.files:
            messagebox.showwarning("Advertencia", "No hay archivos para procesar")
            return
        
        self.btn_process.config(state=tk.DISABLED)
        self.btn_download.config(state=tk.DISABLED)
        thread = threading.Thread(target=self.process_files_thread)
        thread.daemon = True
        thread.start()
    
    def download_pdf(self):
        """Abrir ubicación del PDF generado"""
        if self.output_pdf and os.path.exists(self.output_pdf):
            os.startfile(os.path.dirname(self.output_pdf))
            messagebox.showinfo("Descarga", f"PDF guardado en:\n{self.output_pdf}")
        else:
            messagebox.showerror("Error", "No se encontró el archivo PDF")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = WatermarkRemoverApp(root)
    root.mainloop()