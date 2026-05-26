import pandas as pd

data = {
    'name': [
        'Lavender', 'Rosemary', 'Thyme', 'Basil', 'Mint',
        'Cilantro', 'Parsley', 'Sage', 'Oregano', 'Chives',
        'Dill', 'Fennel', 'Tarragon', 'Marjoram', 'Coriander',
        'Lemongrass', 'Chamomile', 'Echinacea', 'Valerian', 'St. John\'s Wort'
    ],
    'scientific_name': [
        'Lavandula', 'Salvia rosmarinus', 'Thymus vulgaris', 'Ocimum basilicum', 'Mentha',
        'Coriandrum sativum', 'Petroselinum crispum', 'Salvia officinalis', 'Origanum vulgare', 'Allium schoenoprasum',
        'Anethum graveolens', 'Foeniculum vulgare', 'Artemisia dracunculus', 'Origanum majorana', 'Coriandrum sativum',
        'Cymbopogon', 'Matricaria chamomilla', 'Echinacea purpurea', 'Valeriana officinalis', 'Hypericum perforatum'
    ],
    'family': [
        'Lamiaceae', 'Lamiaceae', 'Lamiaceae', 'Lamiaceae', 'Lamiaceae',
        'Apiaceae', 'Apiaceae', 'Lamiaceae', 'Lamiaceae', 'Amaryllidaceae',
        'Apiaceae', 'Apiaceae', 'Asteraceae', 'Lamiaceae', 'Apiaceae',
        'Poaceae', 'Asteraceae', 'Asteraceae', 'Caprifoliaceae', 'Hypericaceae'
    ],
    'genus': [
        'Lavandula', 'Salvia', 'Thymus', 'Ocimum', 'Mentha',
        'Coriandrum', 'Petroselinum', 'Salvia', 'Origanum', 'Allium',
        'Anethum', 'Foeniculum', 'Artemisia', 'Origanum', 'Coriandrum',
        'Cymbopogon', 'Matricaria', 'Echinacea', 'Valeriana', 'Hypericum'
    ],
    'barcode': [f'BAR1{str(i).zfill(2)}' for i in range(20)],
    'description': ['A wonderful medicinal and culinary herb.'] * 20
}

df = pd.DataFrame(data)
df.to_excel('plants_data.xlsx', index=False)
print("Created plants_data.xlsx with 20 records.")
