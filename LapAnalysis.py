import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import chardet
from io import StringIO
import subprocess
import os

filename = ""
ResultsFile = ""
Series = None
Session = None
CarNumber= None

def select_sectors_file():
    global filename
    filename = filedialog.askopenfilename(title="Seleziona un file CSV", filetypes=[("File CSV", "*.csv")])
    pathlabel.config(text=filename)

def select_results_file():
    global ResultsFile
    ResultsFile = filedialog.askopenfilename(title="Seleziona un file CSV", filetypes=[("File CSV", "*.csv")])
    pathlabel2.config(text=ResultsFile)

def SeriesSelect(event):
    global Series
    Series = combo.get()

def SessionSelect(event):
    global Session
    Session = combo2.get()

def CarSelect(event):
    global CarNumber
    CarNumber = entry.get()
    if CarNumber.isdigit():  # controlla che sia composto solo da cifre
        CarNumber = int(CarNumber)
    else:
        messagebox.showerror(text="❌ Inserisci solo numeri interi!")

def run_analysis():
    if not filename or not ResultsFile:
        messagebox.showerror("Errore", "Seleziona entrambi i file CSV prima di avviare l'analisi.")
        return

    # --- File 1 ---
    with open(filename, 'rb') as f:
        raw_data = f.read()
        encoding_rilevato = chardet.detect(raw_data)['encoding']

    testo_originale = raw_data.decode(encoding_rilevato, errors='ignore')
    righe = testo_originale.splitlines()
    righe_filtrate = [righe[0]] + [r for r in righe[1:] if not r.strip().startswith("Bib")]
    testo_utf8 = '\n'.join(righe_filtrate).replace(';', ',')
    
    # Ora dividiamo di nuovo in righe per fare il controllo su Lap
    righe_lista = testo_utf8.splitlines()
    
    # Prendiamo l'header
    header = righe_lista[0]
    
    # Indice della colonna Lap (esempio: 2)
    lap_index = 7
    
    righe_finali = [header]

    # Cicliamo su righe dalla 1 alla penultima per confrontare i con i+1
    for i in range(1, len(righe_lista)-1):
        valori_correnti = righe_lista[i].split(',')
        valori_successivi = righe_lista[i+1].split(',')
    
        # Controlliamo se Lap è uguale
        if valori_correnti[lap_index] != valori_successivi[lap_index]:
            righe_finali.append(righe_lista[i])
    
    # Aggiungiamo sempre l'ultima riga (non ha una successiva con cui confrontare)
    righe_finali.append(righe_lista[-1])
    
    # Ora testo finale
    testo_finale = '\n'.join(righe_finali)

    # --- File 2 ---
    with open(ResultsFile, 'rb') as f:
        raw_data = f.read()
        encoding_rilevato = chardet.detect(raw_data)['encoding']
    Results_utf8 = raw_data.decode(encoding_rilevato, errors='ignore').replace(';', ',')

    # --- Salvataggio ---
    df = pd.read_csv(StringIO(testo_finale))
    Results = pd.read_csv(StringIO(Results_utf8))
    info = pd.DataFrame([[Session, CarNumber]], columns=["Sessione", "Car"])

    df.to_csv("df.csv", index=False)
    Results.to_csv("results.csv", index=False)
    info.to_csv("info.csv",index= False)

    # --- Avvia l'altro script ---
    try:
        subprocess.run(["python", "2025_GTWCE_RaceAnalysis_End.py"], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Errore", f"Lo script si è interrotto con un errore:\n{e}")
    except FileNotFoundError:
        messagebox.showerror("Errore", "Il file 2025_GTWCE_RaceAnalysis_End.py non è stato trovato.")

def chiudi_finestra():
    finestra.destroy()

# === INTERFACCIA ===
finestra = tk.Tk()
finestra.configure(background='dark green')
finestra.geometry("1500x500")
finestra.title("Laptime Analysis")

# File 1
browsebutton = tk.Button(finestra, text="Sectors Analysis (CSV File)", command=select_sectors_file)
browsebutton.place(x=20, y=100)
pathlabel = tk.Label(finestra, bg='dark green', fg='white')
pathlabel.place(x=180, y=100)

# File 2
browsebutton2 = tk.Button(finestra, text="Results File (CSV File)", command=select_results_file)
browsebutton2.place(x=20, y=150)
pathlabel2 = tk.Label(finestra, bg='dark green', fg='white')
pathlabel2.place(x=180, y=150)

# Combobox
opzioni = ["GTWCE Endurance", "GTWCE Sprint", "Ciao", "Prova"]
combo = ttk.Combobox(finestra, values=opzioni, state="readonly")
combo.current(0)
combo.place(x=20, y=200)
combo.bind("<<ComboboxSelected>>", SeriesSelect)

# Combobox 2 per Scelta Sessione
Session_option = ["FP / PQ", "Qualy", "Race"]
combo2 = ttk.Combobox(finestra, values=Session_option, state="readonly")
combo2.current(0)
combo2.place(x=180, y=200)
combo2.bind("<<ComboboxSelected>>", SessionSelect)

# Scegli Reference Car
entry = tk.Entry(finestra)
entry.place(x=250, y=250)
entry.bind("<Return>", CarSelect)
label = tk.Label(finestra, text="Insert Car Number and press Enter (Invio):")
label.configure(background='dark green')
label.place(x=20, y=250)

# Pulsanti
btn_run = tk.Button(finestra, text="Avvia Analisi", command=run_analysis)
btn_run.place(x=20, y=300)

btn_chiudi = tk.Button(finestra, text="Chiudi", command=chiudi_finestra)
btn_chiudi.place(x=120, y=300)

finestra.mainloop()

import platform

DEBUG = False
PORT = 8051

def kill_process_using_port(port):
    if platform.system() == "Windows":
        try:
            result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            lines = result.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids.add(pid)

            for pid in pids:
                print(f"Terminando processo PID {pid} sulla porta {port}...")
                os.system(f'taskkill /PID {pid} /F')
        except subprocess.CalledProcessError:
            print(f"Nessun processo in ascolto sulla porta {port}.")
    else:
        print("Supportato solo su Windows")
