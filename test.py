import pandas as pd
import math


df = pd.read_csv("test_pogoda.csv")
print(df)
print("Ilość linij: ", len(df))
print("Nazwy kolumn: ", df.columns.tolist())

print("Unikalne wartości: ")
for kolumna in df.columns:
    print(f"{kolumna}: {df[kolumna].unique()}")

print("Puste komurki: ")
print(df.isnull().sum())

print("Ilość decyzji: ")
print(df["Decyzja"].value_counts())

decyzje = df["Decyzja"].value_counts()
total = len(df)
print("Oblicznie entropii: ")
entropia = 0
for klasa, liczba in decyzje.items():
    p = liczba/total
    entropia -= p*math.log2(p)
    print(f' {klasa}: {liczba}/{total} = {p:.3f}')
print(f"Entropia: {entropia:.4f}")

print("Zysk informacyjny dla atrybutu pogoda: ")
for wartosc in df["Pogoda"].unique():
    podzbior = df[df["Pogoda"] == wartosc]
    print(f"Pogoda = {wartosc} ({len(podzbior)} wierszy):")
    print(podzbior["Decyzja"].value_counts().to_string())

print("Obliczanie zysku informatycznego dla pogoda: ")
entropia_po_podziale = 0
for wartosc in df["Pogoda"].unique():
    podzbior = df[df["Pogoda"] == wartosc]
    waga = len(podzbior)/len(df)
    e = 0
    for klasa, liczba in podzbior["Decyzja"].value_counts().items():
        p = liczba/len(podzbior)
        if p >0:
            e -= p*math.log2(p)
    entropia_po_podziale += waga*e
    print(f'{wartosc}: waga = {waga:.3f}, entropia={e:.4f}')

zysk = entropia-entropia_po_podziale
print(f"Entropia przed podzialem:{entropia:.4f}")
print(f"Entropia po podziale:{entropia_po_podziale:.4f}")
print(f"Zysk informacyjny: {zysk:.4f}")

print("Zysk informacyjny dla wszystkich atrybutów: ")
atrybuty = ["Pogoda", "Temperatura", "Wiatr", "Wilgotnosc", "Opady"]
wyniki ={}
for atrybut in atrybuty:
    entropia_po =0
    for wartosc in df[atrybut].unique():
        podzbior = df[df[atrybut] == wartosc]
        waga = len(podzbior)/len(df)
        e=0
        for klasa, liczba in podzbior["Decyzja"].value_counts().items():
            p = liczba/len(podzbior)
            if p >0:
                e -= p*math.log2(p)
            entropia_po += waga*e
        zysk = entropia - entropia_po
        wyniki[atrybut] = round(zysk, 4)
for atrybut, zysk in sorted(wyniki.items(), key=lambda x: x[1], reverse=True):
    print(f'{atrybut}: {zysk}')
najlepszy= max(wyniki, key = wyniki.get)
print(f"Najlepszy atrybut(korzen drzewa): {najlepszy}")


