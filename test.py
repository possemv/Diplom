import pandas as pd
import math

df = pd.read_csv("test_pogoda.csv", index_col=0)
print(df)

print("\nSpojnosc:")
decision_col = df.columns[-1]
condition_cols = list(df.columns[:-1])
konflikty = []
for a in range(len(df)):
    for b in range(a + 1, len(df)):
        wiersz1 = df.iloc[a]
        wiersz2 = df.iloc[b]
        warunki_same = all(wiersz1[col] == wiersz2[col] for col in condition_cols)
        decyzje_inne = wiersz1[decision_col] != wiersz2[decision_col]

        if warunki_same and decyzje_inne:
            konflikty.append((a, b))
if len(konflikty) ==0:
    print("Tablica jest spojna")
else:
    print("Tablica nie jest spojna, bo zostal znaleziony konflikt.")
    for a, b in konflikty:
        print(f"Wiersze {a} i {b} maja te same wartosci, ale rozne decyzje")
        print(f"Wiersz {a}: {dict(df.iloc[a])}")
        print(f"Wiersz {b}: {dict(df.iloc[b])}")

print("\nIlość linij: ", len(df))
print("Nazwy kolumn: ", df.columns.tolist())

print("\nUnikalne wartości: ")
for kolumna in df.columns:
    print(f"{kolumna}: {df[kolumna].unique().tolist()}")

print("\nPuste komurki: ")
for kolumna, liczba in df.isnull().sum().items():
    print(f"{kolumna}:{liczba}")

print("\nRozklad decyzji w procentach: ")
decyzje = df["Decyzja"].value_counts()
total = len(df)
for klasa, liczba in decyzje.items():
    procent = round(liczba/total*100, 1)
    print(f"{klasa}:{liczba} razy ({procent}%)")

print("\nOblicznie entropii: ")
decyzje = df["Decyzja"].value_counts()
total = len(df)
entropia = 0
for klasa, liczba in decyzje.items():
    p = liczba/total
    entropia -= p*math.log2(p)
print(f"Entropia glowna: {round(entropia, 4)}")

najlepszy_atrybut = None
najlepszy_zysk = -1
for kolumna in condition_cols:
    entropia_atrybutu = 0
    for wartosc in df[kolumna].unique():
        podzbior = df[df[kolumna] == wartosc]
        waga = len(podzbior)/total

    entropia_podzbior = 0
    for klasa, liczba in podzbior["Decyzja"].value_counts().items():
        p = liczba/len(podzbior)
        entropia_podzbior -=p*math.log2(p)
    entropia_atrybutu += waga*entropia_podzbior

    zysk = entropia - entropia_atrybutu
    print(f"{kolumna}:")
    print(f"Entropia atrybutu: {round(entropia_atrybutu, 4)}")
    print(f"Zysk informacyjny: {round(zysk, 4)}\n")

    if zysk > najlepszy_zysk:
        najlepszy_zysk = zysk
        najlepszy_atrybut = kolumna
print(f"Najlepszy atrybut: '{najlepszy_atrybut}' (zysk = {round(najlepszy_zysk, 4)})")


