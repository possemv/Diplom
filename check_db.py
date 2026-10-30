import db

db.create_tables()
print('Tabela jest gotowa')

db.save_table('test_pogoda.csv', True, 'Decyzja')
db.save_table('inne_dane.csv', False, 'Wynik')
db.save_table('test_pogoda.csv', True, 'Decyzja')   # ten sam plik drugi raz - nie powinno być duplikatu

print('Ostatnie tabele:')
for table in db.get_recent_tables():
    print(' ', table['id'], table['filename'], table['decision_col'], table['last_used'])

print('Tabela o id 1:', db.get_table(1))
print('Tabela o id 999:', db.get_table(999))