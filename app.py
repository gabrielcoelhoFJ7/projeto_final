from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from models import Funcionario, Movimentacao, Produto, Categoria, db_session
from sqlalchemy import select, func, extract
import os
import io
import base64

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/dashboard', methods=['GET'])
def dashboard():
    produtos_por_pagina = 15
    # Obter o número da página a partir da query string (padrão: 1)
    pagina_atual = int(request.args.get('pagina', 1))
    print(pagina_atual)
    # Calcular o offset
    offset = (pagina_atual - 1) * produtos_por_pagina

    # Selecionar os produtos com limite e offset
    lista_produtos = (select(Produto, Categoria)
                      .join(Categoria, Categoria.id_categoria == Produto.id_categoria)
                      .offset(offset).limit(produtos_por_pagina))
    lista_produtos = db_session.execute(lista_produtos).fetchall()

    total_veterinarios = db_session.query(Produto).count()
    total_paginas = (total_veterinarios + produtos_por_pagina - 1) // produtos_por_pagina

    return render_template('dashboard.html',
                           cavalo=lista_produtos,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas
                           )
@app.route('/funcionario', methods=['GET'])
def funcionario():
    produtos_por_pagina = 15
    # Obter o número da página a partir da query string (padrão: 1)
    pagina_atual = int(request.args.get('pagina', 1))
    print(pagina_atual)
    # Calcular o offset
    offset = (pagina_atual - 1) * produtos_por_pagina

    # Selecionar os produtos com limite e offset
    lista_produtos = (select(Funcionario)
                      .offset(offset).limit(produtos_por_pagina))
    lista_produtos = db_session.execute(lista_produtos).fetchall()

    total_veterinarios = db_session.query(Produto).count()
    total_paginas = (total_veterinarios + produtos_por_pagina - 1) // produtos_por_pagina

    return render_template('funcionario.html',
                           cavalo=lista_produtos,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas
                           )

@app.route('/produto', methods=['GET'])
def produto():
    produtos_por_pagina = 10
    # Obter o número da página a partir da query string (padrão: 1)
    pagina_atual = int(request.args.get('pagina', 1))
    print(pagina_atual)
    # Calcular o offset
    offset = (pagina_atual - 1) * produtos_por_pagina

    # Selecionar os produtos com limite e offset
    lista_produtos = (select(Produto, Categoria)
                      .join(Categoria, Categoria.id_categoria == Produto.id_categoria)
                      .offset(offset).limit(produtos_por_pagina))
    lista_produtos = db_session.execute(lista_produtos).fetchall()

    total_veterinarios = db_session.query(Produto).count()
    total_paginas = (total_veterinarios + produtos_por_pagina - 1) // produtos_por_pagina

    return render_template('produto.html',
                           cavalo=lista_produtos,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas
                           )


@app.route('/exemplo')
def exemplo():
    return render_template('exemplo.html')


if __name__ == '__main__':
    app.run(debug=True)
