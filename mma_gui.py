import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import requests
from io import BytesIO
from mma_prob_model import FighterStats, win_probability, bootstrap_probability, explain
from ufc_fighter_scraper import UFCFighterScraper

class MMAAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MMA Fight Probability Analyzer")
        self.root.geometry("1600x900")
        self.root.configure(bg='#2c3e50')
        
        # Variáveis para armazenar as imagens dos lutadores
        self.fighter1_image = None
        self.fighter2_image = None
        
        # Inicializar scraper
        self.scraper = UFCFighterScraper()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(40, 20))  # 20px a mais no topo
        
        # Título
        title_label = tk.Label(main_frame, text="MMA-STATISTICS", 
                              font=("Arial", 24, "bold"), 
                              fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(0, 30))
        
        # Frame central com os lutadores
        center_frame = tk.Frame(main_frame, bg='#2c3e50')
        center_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame esquerdo completo (Inputs do Lutador 1)
        left_section = tk.Frame(center_frame, bg='#2c3e50')
        left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Frame central para fotos e VS (layout horizontal)
        center_photos_frame = tk.Frame(center_frame, bg='#2c3e50', width=600)
        center_photos_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        center_photos_frame.pack_propagate(False)
        
        # Frame direito completo (Inputs do Lutador 2)
        right_section = tk.Frame(center_frame, bg='#2c3e50')
        right_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Configurar lutador 1 (esquerda - apenas inputs)
        self.setup_fighter_inputs(left_section, "FIGHTER 1", 1)
        
        # Configurar seção central com fotos e VS
        self.setup_center_photos_vs(center_photos_frame)
        
        # Configurar lutador 2 (direita - apenas inputs)
        self.setup_fighter_inputs(right_section, "FIGHTER 2", 2)
        
        # Frame para resultados detalhados
        results_frame = tk.Frame(main_frame, bg='#2c3e50')
        results_frame.pack(fill=tk.X, pady=(30, 0))
        
        # Label para análise detalhada
        self.detailed_label = tk.Label(results_frame, text="Click CALCULATE to analyze the fight", 
                                      font=("Arial", 12),
                                      fg='#bdc3c7', bg='#2c3e50')
        self.detailed_label.pack(pady=10)
        
        # Frame para contribuições
        self.contrib_frame = tk.Frame(results_frame, bg='#2c3e50')
        self.contrib_frame.pack(fill=tk.X, pady=10)
    
    def setup_fighter_inputs(self, parent, title, fighter_num):
        # Frame com borda escura para os inputs
        inputs_frame = tk.Frame(parent, bg='#34495e', relief=tk.SOLID, bd=2, highlightbackground='#1a252f', highlightthickness=2)
        inputs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Título do lutador
        title_label = tk.Label(inputs_frame, text=title, 
                              font=("Arial", 16, "bold"),
                              fg='#ecf0f1', bg='#34495e')
        title_label.pack(pady=(10, 5))
        
        # Frame para URL do lutador
        url_frame = tk.Frame(inputs_frame, bg='#34495e')
        url_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(url_frame, text="Fighter URL:", font=("Arial", 10, "bold"),
                fg='#ecf0f1', bg='#34495e').pack(anchor=tk.W)
        
        # Container para URL e botão
        url_container = tk.Frame(url_frame, bg='#34495e')
        url_container.pack(fill=tk.X, pady=2)
        
        url_entry = tk.Entry(url_container, font=("Arial", 10))
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        search_btn = tk.Button(url_container, text="SEARCH", 
                             font=("Arial", 9, "bold"),
                             bg='#3498db', fg='white',
                             command=lambda: self.search_fighter(fighter_num, url_entry.get()))
        search_btn.pack(side=tk.RIGHT)
        
        # Frame para nome
        name_frame = tk.Frame(inputs_frame, bg='#34495e')
        name_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(name_frame, text="Fighter Name:", font=("Arial", 10, "bold"),
                fg='#ecf0f1', bg='#34495e').pack(anchor=tk.CENTER)
        
        # Container para centralizar o campo de nome
        name_container = tk.Frame(name_frame, bg='#34495e')
        name_container.pack(fill=tk.X, pady=2)
        
        name_entry = tk.Entry(name_container, font=("Arial", 12), width=25, justify='center')
        name_entry.pack(anchor=tk.CENTER)
        
        # Frame principal para estatísticas
        stats_main_frame = tk.Frame(inputs_frame, bg='#34495e')
        stats_main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=0)
        
        # Criar campos de entrada para estatísticas organizados em seções
        stats_fields = [
            ("STRIKING", [
                ("SLPM", "slpm", "Significant strikes landed per minute"),
                ("SAPM", "sapm", "Significant strikes absorbed per minute"),
                ("Strike Acc (%)", "strike_acc", "Striking accuracy percentage"),
                ("Strike Def (%)", "strike_def", "Striking defense percentage"),
            ]),
            ("GRAPPLING", [
                ("TD Avg/15min", "td_avg15", "Takedowns landed per 15 minutes"),
                ("TD Acc (%)", "td_acc", "Takedown accuracy percentage"),
                ("TD Def (%)", "td_def", "Takedown defense percentage"),
                ("Sub Avg/15min", "sub_avg15", "Submission attempts per 15 minutes"),
            ]),
            ("POWER & ENDURANCE", [
                ("KD Avg/15min", "kd_avg", "Knockdowns per 15 minutes"),
                ("Fight Time (min)", "aft_minutes", "Average fight time in minutes"),
                ("Top 10 Fights", "top10_fights", "Number of fights against UFC Top 10 opponents"),
            ])
        ]
        
        entries = {}
        
        for section_title, fields in stats_fields:
            # Seção título
            section_frame = tk.Frame(stats_main_frame, bg='#34495e')
            section_frame.pack(fill=tk.X, pady=(15, 5))
            
            section_label = tk.Label(section_frame, text=section_title, 
                                   font=("Arial", 11, "bold"),
                                   fg='#3498db', bg='#34495e')
            section_label.pack()
            
            # Separador visual
            separator = tk.Frame(section_frame, height=1, bg='#3498db')
            separator.pack(fill=tk.X, padx=20, pady=2)
            
            # Campos da seção em grid 2x2
            grid_frame = tk.Frame(stats_main_frame, bg='#34495e')
            grid_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for i, (label_text, field_name, tooltip) in enumerate(fields):
                row = i // 2
                col = i % 2
                
                field_frame = tk.Frame(grid_frame, bg='#34495e')
                field_frame.grid(row=row, column=col, sticky="ew", padx=5, pady=3)
                
                # Configurar colunas para expandir igualmente
                grid_frame.grid_columnconfigure(0, weight=1)
                grid_frame.grid_columnconfigure(1, weight=1)
                
                label = tk.Label(field_frame, text=label_text, 
                               font=("Arial", 9, "bold"),
                               fg='#ecf0f1', bg='#34495e')
                label.pack(anchor=tk.W)
                
                entry = tk.Entry(field_frame, font=("Arial", 10), width=15)
                entry.pack(fill=tk.X, pady=2)
                entries[field_name] = entry
                
                # Tooltip
                self.create_tooltip(entry, tooltip)
        
        # Armazenar referências
        if fighter_num == 1:
            self.fighter1_entries = entries
            self.fighter1_name = name_entry
            self.fighter1_url = url_entry
        else:
            self.fighter2_entries = entries
            self.fighter2_name = name_entry
            self.fighter2_url = url_entry
    
    def setup_center_photos_vs(self, parent):
        # Frame principal para centralização completa
        main_center_frame = tk.Frame(parent, bg='#2c3e50')
        main_center_frame.pack(expand=True, fill=tk.BOTH)
        
        # Frame para organizar horizontalmente: Foto1, VS+Probs+Button, Foto2
        content_frame = tk.Frame(main_center_frame, bg='#2c3e50')
        content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # Centralização absoluta
        
        # Foto do Fighter 1 (esquerda do VS) - centralizada verticalmente
        photo1_frame = tk.Frame(content_frame, bg='#2c3e50')
        photo1_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        # Centralizar label do fighter 1
        fighter1_label = tk.Label(photo1_frame, text="FIGHTER 1", 
                                font=("Arial", 12, "bold"),
                                fg='#ecf0f1', bg='#2c3e50')
        fighter1_label.pack(pady=(0, 10))
        
        # Frame fixo para a imagem com tamanho constante - centralizado
        image1_container = tk.Frame(photo1_frame, bg='#34495e', width=150, height=220, 
                                   relief=tk.SOLID, bd=2, highlightbackground='#1a252f', highlightthickness=2)
        image1_container.pack()
        image1_container.pack_propagate(False)  # Impede redimensionamento
        
        self.fighter1_image_label = tk.Label(image1_container, text="Click to add\nfighter photo", 
                                           font=("Arial", 11),
                                           fg='#bdc3c7', bg='#34495e',
                                           anchor=tk.CENTER)
        self.fighter1_image_label.pack(fill=tk.BOTH, expand=True)
        self.fighter1_image_label.bind("<Button-1>", lambda e: self.add_fighter_image(1, self.fighter1_image_label))
        
        # Labels abaixo da foto do Fighter 1 (inicialmente vazios)
        self.fighter1_name_result = tk.Label(photo1_frame, text="", 
                                           font=("Arial", 12, "bold"),
                                           fg='#ecf0f1', bg='#2c3e50',
                                           anchor=tk.CENTER)
        self.fighter1_name_result.pack(pady=(10, 2))
        
        self.fighter1_prob_result = tk.Label(photo1_frame, text="", 
                                           font=("Arial", 16, "bold"),
                                           fg='#27ae60', bg='#2c3e50',
                                           anchor=tk.CENTER)
        self.fighter1_prob_result.pack(pady=2)
        
        # Seção VS central com probabilidades - perfeitamente centralizada
        vs_frame = tk.Frame(content_frame, bg='#2c3e50')
        vs_frame.pack(side=tk.LEFT, padx=40)
        
        # Container para centralizar todos os elementos do VS
        vs_content = tk.Frame(vs_frame, bg='#2c3e50')
        vs_content.pack(expand=True, fill=tk.BOTH)
        
        # Label VS no centro absoluto
        vs_label = tk.Label(vs_content, text="VS", 
                           font=("Arial", 52, "bold"),
                           fg='#e74c3c', bg='#2c3e50',
                           anchor=tk.CENTER)
        vs_label.pack(pady=(50, 30))
        
        # Botão de análise - centralizado
        self.analyze_btn = tk.Button(vs_content, text="CALCULATE", 
                                    font=("Arial", 12, "bold"),
                                    bg='#e74c3c', fg='white',
                                    command=self.analyze_fight,
                                    height=2, width=12)
        self.analyze_btn.pack(pady=15)
        
        # Label para intervalo de confiança - centralizado
        self.confidence_label = tk.Label(vs_content, text="", 
                                        font=("Arial", 9),
                                        fg='#bdc3c7', bg='#2c3e50',
                                        anchor=tk.CENTER)
        self.confidence_label.pack(pady=(10, 50))
        
        # Foto do Fighter 2 (direita do VS) - centralizada verticalmente
        photo2_frame = tk.Frame(content_frame, bg='#2c3e50')
        photo2_frame.pack(side=tk.LEFT, padx=(30, 0))
        
        # Centralizar label do fighter 2
        fighter2_label = tk.Label(photo2_frame, text="FIGHTER 2", 
                                font=("Arial", 12, "bold"),
                                fg='#ecf0f1', bg='#2c3e50')
        fighter2_label.pack(pady=(0, 10))
        
        # Frame fixo para a imagem com tamanho constante - centralizado
        image2_container = tk.Frame(photo2_frame, bg='#34495e', width=150, height=220, 
                                   relief=tk.SOLID, bd=2, highlightbackground='#1a252f', highlightthickness=2)
        image2_container.pack()
        image2_container.pack_propagate(False)  # Impede redimensionamento
        
        self.fighter2_image_label = tk.Label(image2_container, text="Click to add\nfighter photo", 
                                           font=("Arial", 11),
                                           fg='#bdc3c7', bg='#34495e',
                                           anchor=tk.CENTER)
        self.fighter2_image_label.pack(fill=tk.BOTH, expand=True)
        self.fighter2_image_label.bind("<Button-1>", lambda e: self.add_fighter_image(2, self.fighter2_image_label))
        
        # Labels abaixo da foto do Fighter 2 (inicialmente vazios)
        self.fighter2_name_result = tk.Label(photo2_frame, text="", 
                                           font=("Arial", 12, "bold"),
                                           fg='#ecf0f1', bg='#2c3e50',
                                           anchor=tk.CENTER)
        self.fighter2_name_result.pack(pady=(10, 2))
        
        self.fighter2_prob_result = tk.Label(photo2_frame, text="", 
                                           font=("Arial", 16, "bold"),
                                           fg='#27ae60', bg='#2c3e50',
                                           anchor=tk.CENTER)
        self.fighter2_prob_result.pack(pady=2)
    
    def create_tooltip(self, widget, text):
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, 
                           font=("Arial", 9),
                           bg="#f39c12", fg="white",
                           wraplength=200)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def search_fighter(self, fighter_num, url):
        """Buscar dados do lutador pela URL usando o scraper"""
        if not url.strip():
            messagebox.showwarning("Warning", "Please enter a fighter URL")
            return
        
        try:
            # Mostrar indicador de carregamento
            if fighter_num == 1:
                self.fighter1_name.delete(0, tk.END)
                self.fighter1_name.insert(0, "Loading...")
            else:
                self.fighter2_name.delete(0, tk.END)
                self.fighter2_name.insert(0, "Loading...")
            
            # Atualizar interface
            self.root.update()
            
            # Buscar dados do lutador
            fighter_data = self.scraper.get_fighter_data(url)
            
            if not fighter_data or 'name' not in fighter_data:
                messagebox.showerror("Error", "Could not extract fighter data from the URL")
                return
            
            # Preencher nome
            if fighter_num == 1:
                entries = self.fighter1_entries
                name_entry = self.fighter1_name
                image_label = self.fighter1_image_label
            else:
                entries = self.fighter2_entries
                name_entry = self.fighter2_name
                image_label = self.fighter2_image_label
            
            # Limpar e preencher nome
            name_entry.delete(0, tk.END)
            name_entry.insert(0, fighter_data.get('name', 'Unknown Fighter'))
            
            # Preencher estatísticas
            stat_mapping = {
                'slpm': 'slpm',
                'sapm': 'sapm', 
                'strike_acc': 'strike_acc',
                'strike_def': 'strike_def',
                'td_avg15': 'td_avg15',
                'td_acc': 'td_acc',
                'td_def': 'td_def',
                'sub_avg15': 'sub_avg15',
                'kd_avg': 'kd_avg',
                'aft_minutes': 'aft_minutes'
            }
            
            for field_name, entry in entries.items():
                if field_name in stat_mapping:
                    value = fighter_data.get(stat_mapping[field_name])
                    entry.delete(0, tk.END)
                    if value is not None:
                        # Converter frações para percentuais se necessário
                        if field_name in ['strike_acc', 'strike_def', 'td_acc', 'td_def']:
                            if isinstance(value, (int, float)) and value <= 1.0:
                                value = value * 100
                        entry.insert(0, f"{value:.2f}" if isinstance(value, float) else str(value))
            
            # Carregar imagem se disponível
            if fighter_data.get('image_url'):
                self.load_fighter_image_from_url(fighter_num, fighter_data['image_url'], image_label)
            else:
                print("Nenhuma URL de imagem encontrada para este lutador")
            
            messagebox.showinfo("Success", f"Fighter data loaded successfully for {fighter_data.get('name')}")
            
        except Exception as e:
            # Limpar campo de nome em caso de erro
            if fighter_num == 1:
                self.fighter1_name.delete(0, tk.END)
            else:
                self.fighter2_name.delete(0, tk.END)
            
            messagebox.showerror("Error", f"Failed to load fighter data: {str(e)}")
    
    def load_fighter_image_from_url(self, fighter_num, image_url, label):
        """Carregar imagem do lutador a partir de uma URL"""
        try:
            # Headers para evitar bloqueios 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Tentar diferentes variações da URL se necessário
            urls_to_try = [image_url]
            
            # Se a URL contém parâmetros, tentar sem eles
            if '?' in image_url:
                base_url = image_url.split('?')[0]
                urls_to_try.append(base_url)
            
            # Se é uma URL da UFC, tentar versões alternativas
            if 'ufc.com' in image_url:
                # Tentar versão sem itok
                if 'itok=' in image_url:
                    clean_url = image_url.split('?itok=')[0]
                    urls_to_try.append(clean_url)
                
                # Tentar versão com .com.br
                if '.com/' in image_url:
                    br_url = image_url.replace('.com/', '.com.br/')
                    urls_to_try.append(br_url)
            
            image = None
            successful_url = None
            
            # Tentar cada URL até encontrar uma que funcione
            for url in urls_to_try:
                try:
                    print(f"Tentando carregar imagem de: {url}")
                    response = requests.get(url, headers=headers, timeout=15, stream=True)
                    
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        successful_url = url
                        print(f"Imagem carregada com sucesso de: {url}")
                        break
                    else:
                        print(f"Erro {response.status_code} para URL: {url}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"Erro de request para {url}: {str(e)}")
                    continue
                except Exception as e:
                    print(f"Erro ao processar {url}: {str(e)}")
                    continue
            
            if image is None:
                print("Nenhuma URL de imagem funcionou")
                return
            
            # Redimensionar para o container
            container_width = 144
            container_height = 244
            
            img_width, img_height = image.size
            scale_w = container_width / img_width
            scale_h = container_height / img_height
            scale = min(scale_w, scale_h)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            image_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Criar imagem final com fundo escuro
            final_image = Image.new('RGB', (container_width, container_height), '#34495e')
            paste_x = (container_width - new_width) // 2
            paste_y = (container_height - new_height) // 2
            
            # Tratar transparência se necessário
            if image_resized.mode in ('RGBA', 'LA') or (image_resized.mode == 'P' and 'transparency' in image_resized.info):
                if image_resized.mode != 'RGBA':
                    image_resized = image_resized.convert('RGBA')
                
                temp_bg = Image.new('RGBA', (new_width, new_height), '#34495e')
                composed = Image.alpha_composite(temp_bg, image_resized)
                image_resized = composed.convert('RGB')
            
            final_image.paste(image_resized, (paste_x, paste_y))
            
            photo = ImageTk.PhotoImage(final_image)
            
            # Atualizar label
            label.configure(image=photo, text="")
            label.image = photo
            
            # Armazenar imagem
            if fighter_num == 1:
                self.fighter1_image = photo
            else:
                self.fighter2_image = photo
            
            print(f"Imagem do Fighter {fighter_num} carregada com sucesso!")
                
        except Exception as e:
            print(f"Erro geral ao carregar imagem: {str(e)}")
            # Manter o texto padrão se não conseguir carregar a imagem
    
    def add_fighter_image(self, fighter_num, label):
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title=f"Select Fighter {fighter_num} Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        
        if filename:
            try:
                # Carregar imagem original
                image = Image.open(filename)
                
                # Redimensionar para o container 150x250 (deixar 3px de margem: 144x244)
                container_width = 144
                container_height = 244
                
                # Calcular redimensionamento mantendo proporção
                img_width, img_height = image.size
                scale_w = container_width / img_width
                scale_h = container_height / img_height
                scale = min(scale_w, scale_h)  # Usar a menor escala para manter dentro dos limites
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Redimensionar a imagem
                image_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Criar uma imagem com fundo escuro da interface
                final_image = Image.new('RGB', (container_width, container_height), '#34495e')
                paste_x = (container_width - new_width) // 2
                paste_y = (container_height - new_height) // 2
                
                # Se a imagem tem transparência (canal alpha), compor corretamente com o fundo
                if image_resized.mode in ('RGBA', 'LA') or (image_resized.mode == 'P' and 'transparency' in image_resized.info):
                    # Converter para RGBA se necessário
                    if image_resized.mode != 'RGBA':
                        image_resized = image_resized.convert('RGBA')
                    
                    # Criar uma imagem temporária com fundo escuro para composição
                    temp_bg = Image.new('RGBA', (new_width, new_height), '#34495e')
                    # Compor a imagem com transparência sobre o fundo escuro
                    composed = Image.alpha_composite(temp_bg, image_resized)
                    # Converter para RGB
                    image_resized = composed.convert('RGB')
                
                final_image.paste(image_resized, (paste_x, paste_y))
                
                photo = ImageTk.PhotoImage(final_image)
                
                # Atualizar label
                label.configure(image=photo, text="")
                label.image = photo  # Manter referência
                
                # Armazenar imagem
                if fighter_num == 1:
                    self.fighter1_image = photo
                else:
                    self.fighter2_image = photo
                    
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {str(e)}")
    
    def get_fighter_stats(self, entries):
        """Extrair estatísticas dos campos de entrada"""
        try:
            stats = {}
            for field, entry in entries.items():
                value = entry.get().strip()
                if not value:
                    raise ValueError(f"Field '{field}' is empty")
                
                # Converter percentuais para decimais se necessário
                if field in ['strike_acc', 'strike_def', 'td_acc', 'td_def']:
                    stats[field] = float(value) / 100.0 if float(value) > 1.0 else float(value)
                else:
                    stats[field] = float(value)
            
            return FighterStats(**stats)
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
    
    def analyze_fight(self):
        try:
            # Obter estatísticas dos lutadores
            fighter1_stats = self.get_fighter_stats(self.fighter1_entries)
            fighter2_stats = self.get_fighter_stats(self.fighter2_entries)
            
            # Obter nomes
            fighter1_name = self.fighter1_name.get() or "Fighter 1"
            fighter2_name = self.fighter2_name.get() or "Fighter 2"
            
            # Calcular probabilidades
            p, contrib = win_probability(fighter1_stats, fighter2_stats)
            mean_p, (lo, hi) = bootstrap_probability(fighter1_stats, fighter2_stats, iters=400, noise=0.03)
            
            # Mostrar nome e probabilidade abaixo de cada foto
            self.fighter1_name_result.configure(text=fighter1_name)
            self.fighter1_prob_result.configure(text=f"{p*100:.1f}%")
            
            self.fighter2_name_result.configure(text=fighter2_name)
            self.fighter2_prob_result.configure(text=f"{(1-p)*100:.1f}%")
            
            # Mostrar intervalo de confiança
            self.confidence_label.configure(text=f"CI 90%: [{lo*100:.1f}% - {hi*100:.1f}%]")
            
            # Mostrar análise detalhada
            detailed_text = f"Analysis Complete - {fighter1_name} vs {fighter2_name}"
            self.detailed_label.configure(text=detailed_text, fg='#27ae60')
            
            # Limpar contribuições anteriores
            for widget in self.contrib_frame.winfo_children():
                widget.destroy()
            
            # Mostrar contribuições
            contrib_title = tk.Label(self.contrib_frame, text="Feature Contributions (click for details):", 
                                   font=("Arial", 12, "bold"),
                                   fg='#ecf0f1', bg='#2c3e50')
            contrib_title.pack(pady=(10, 5))
            
            # Botão para mostrar/ocultar contribuições detalhadas
            self.show_details_btn = tk.Button(self.contrib_frame, text="Show Detailed Analysis", 
                                             font=("Arial", 10),
                                             bg='#3498db', fg='white',
                                             command=lambda: self.toggle_contributions(contrib))
            self.show_details_btn.pack(pady=5)
            
            # Frame para contribuições (inicialmente oculto)
            self.contrib_details_frame = tk.Frame(self.contrib_frame, bg='#2c3e50')
            self.contrib_visible = False
            
        except Exception as e:
            # Limpar resultados em caso de erro
            self.confidence_label.configure(text="")
            
            # Limpar resultados abaixo das fotos
            self.fighter1_name_result.configure(text="")
            self.fighter1_prob_result.configure(text="")
            self.fighter2_name_result.configure(text="")
            self.fighter2_prob_result.configure(text="")
            
            self.detailed_label.configure(text=f"Error: {str(e)}", fg='#e74c3c')
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
    
    def toggle_contributions(self, contrib):
        """Mostra/oculta as contribuições detalhadas"""
        if not self.contrib_visible:
            # Mostrar contribuições
            self.contrib_details_frame.pack(fill=tk.X, pady=10)
            
            # Criar frame scrollável para contribuições
            contrib_canvas = tk.Canvas(self.contrib_details_frame, bg='#2c3e50', height=150)
            contrib_scrollbar = ttk.Scrollbar(self.contrib_details_frame, orient="vertical", command=contrib_canvas.yview)
            contrib_inner_frame = tk.Frame(contrib_canvas, bg='#2c3e50')
            
            contrib_inner_frame.bind(
                "<Configure>",
                lambda e: contrib_canvas.configure(scrollregion=contrib_canvas.bbox("all"))
            )
            
            contrib_canvas.create_window((0, 0), window=contrib_inner_frame, anchor="nw")
            contrib_canvas.configure(yscrollcommand=contrib_scrollbar.set)
            
            # Ordenar contribuições por valor absoluto
            sorted_contrib = sorted(contrib.items(), key=lambda x: abs(x[1]), reverse=True)
            
            for feature, value in sorted_contrib:
                if abs(value) > 0.001:  # Só mostrar contribuições significativas
                    color = '#27ae60' if value > 0 else '#e74c3c'
                    contrib_label = tk.Label(contrib_inner_frame, 
                                           text=f"{feature}: {value:+.3f}",
                                           font=("Arial", 10),
                                           fg=color, bg='#2c3e50')
                    contrib_label.pack(anchor=tk.W, padx=20)
            
            contrib_canvas.pack(side="left", fill="both", expand=True)
            contrib_scrollbar.pack(side="right", fill="y")
            
            self.show_details_btn.configure(text="Hide Detailed Analysis")
            self.contrib_visible = True
        else:
            # Ocultar contribuições
            self.contrib_details_frame.pack_forget()
            self.show_details_btn.configure(text="Show Detailed Analysis")
            self.contrib_visible = False

def main():
    root = tk.Tk()
    app = MMAAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
