import pandas as pd
import math

df = pd.read_csv("test_pogoda.csv", index_col=0)
print(df)

#SPÓJNOŚĆ
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

if len(konflikty) == 0:
    print("Tablica jest spojna")
else:
    print("Tablica nie jest spojna, bo zostal znaleziony konflikt.")
    for a, b in konflikty:
        print(f"Wiersze {a} i {b}: {dict(df.iloc[a])} vs {dict(df.iloc[b])}")

#INFORMACJA O TABLICY
print("\nIlosc wierszy:", len(df))
print("Nazwy kolumn: ", df.columns.tolist())

print("\nUnikalne wartości: ")
for kolumna in df.columns:
    print(f"{kolumna}: {df[kolumna].unique().tolist()}")

print("\nPuste komurki: ")
for kolumna, liczba in df.isnull().sum().items():
    print(f"{kolumna}:{liczba}")

print("\nRozklad decyzji: ")
decyzje = df[decision_col].value_counts()
total = len(df)
for klasa, liczba in decyzje.items():
    procent = round(liczba/total*100, 1)
    print(f"{klasa}:{liczba} razy ({procent}%)")

#ID3
def entropia(dane, decision_col):
    total = len(dane)
    if total ==0:
        return 0
    wynik = 0
    for liczba in dane[decision_col].value_counts():
        p = liczba/total
        wynik -= p*math.log2(p)
    return wynik

def zysk_informacyjny(dane, atrybut, decision_col):
    total = len(dane)
    ent_glowna = entropia(dane, decision_col)
    ent_atrybutu = 0
    for wartosc in dane[atrybut].unique():
        podzbior = dane[dane[atrybut] == wartosc]
        waga = len(podzbior)/total
        ent_atrybutu += waga * entropia(podzbior, decision_col)
    return ent_glowna - ent_atrybutu

def id3(dane, atrybuty, decision_col, poziom=0):
    wciecie = " " * poziom
    if len(dane[decision_col].unique()) == 1:
        decyzja = dane[decision_col].iloc[0]
        print(f"{wciecie}[LISC] Decyzja: {decyzja}")
        return {"lisc": True, "decyzja": decyzja}

    if len(atrybuty) == 0:
        decyzja = dane[decision_col].mode[0]
        print(f"{wciecie}[LISC - majoryta] Decyzja: {decyzja}")
        return {"lisc": True, "decyzja": decyzja}

    najlepszy = max(atrybuty, key=lambda a: zysk_informacyjny(dane, a, decision_col))
    zysk = zysk_informacyjny(dane, najlepszy, decision_col)
    print(f"{wciecie}[WEZEL] Atrybut: {najlepszy} (zysk = {round(zysk, 4)})")
    wezel = {"lisc": False, "atrybut": najlepszy, "galezie": {}}

    for wartosc in dane[najlepszy].unique():
        podzbior = dane[dane[najlepszy] == wartosc].drop(columns=[najlepszy])
        nowe_atrybuty = [a for a in atrybuty if a != najlepszy]
        print(f"{wciecie} |- {najlepszy} = {wartosc}")

        if len(podzbior) == 0:
            decyzja = dane[decision_col].mode()[0]
            print(f"{wciecie} [LISC - pusty] Decyzja:{decyzja}")
            wezel["galezie"][wartosc] = {"lisc": True, "decyzja": decyzja}
        else:
            wezel["galezie"][wartosc] = id3(podzbior, nowe_atrybuty, decision_col, poziom + 2)
    return wezel

print("\nBudowanie drzewa ID3")
drzewo = id3(df, condition_cols, decision_col)

def generuj_reguly(wezel, sciezka=[], reguly=[]):
    if wezel["lisc"]:
        regula = " AND ".join([f"{a} = {v}" for a, v in sciezka])
        reguly.append((regula, wezel["decyzja"]))
    else:
        for wartosc, podwezel in wezel["galezie"].items():
            generuj_reguly(podwezel, sciezka +[(wezel["atrybut"], wartosc)], reguly)
    return reguly

print("\nReguly decyzyjne:")
reguly = generuj_reguly(drzewo)
for i, (warunek, decyzja) in enumerate(reguly, 1):
    print(f"R{i}: IF {warunek} THEN Decyzja = {decyzja}")

#Statystyka
dlugosci = [len(r[0].split(" AND ")) for r in reguly]
print(f"\nStatystyka:")
print(f"Liczba regul: {len(reguly)}")
print(f"Liczba unikalnych: {len(set(r[0] for r in reguly))}")
print(f"Min dlugosc: {min(dlugosci)}")
print(f"Srednia dlugosc: {round(sum(dlugosci)/len(dlugosci), 2)}")
print(f"Max dlugosc: {max(dlugosci)}")

