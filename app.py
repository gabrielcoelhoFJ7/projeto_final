from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from models import Funcionario, Movimentacao, Produto, Categoria, db_session
from datetime import datetime
from sqlalchemy import select, func, extract
import locale
import os
import plotly.express as px
import plotly.io as pio
import pandas as pd
import io
import base64
from utils import produtos_por_mes_ano

app = Flask(__name__)
app.secret_key = os.urandom(24)
# Configurar idioma para português
# app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')  # Configura o idioma para português


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/dashboard', methods=['GET'])
def dashboard():
    produtos_por_pagina = 15
    pagina_atual = int(request.args.get('pagina', 1))
    offset = (pagina_atual - 1) * produtos_por_pagina

    # Obter total de produtos
    total_produtos = db_session.query(func.sum(Produto.qtd)).scalar()

    # Obter total de funcionários
    total_funcionarios = db_session.query(Funcionario).count()

    # Obter movimentações recentes
    movimentacoes_recentes = (select(Movimentacao, Funcionario, Produto)
                              .join(Funcionario, Funcionario.id_funcionario == Movimentacao.id_funcionario)
                              .join(Produto, Produto.id_produto == Movimentacao.id_produto)
                              .order_by(Movimentacao.data_da_movimentacao.desc())
                              .limit(5))
    movimentacoes_recentes = db_session.execute(movimentacoes_recentes).fetchall()

    # Formatar datas no formato extenso
    movimentacoes_formatadas = []
    for movimentacao, funcionario, produto in movimentacoes_recentes:
        movimentacao.data_extenso = movimentacao.data_da_movimentacao.strftime('%d de %B de %Y')
        movimentacoes_formatadas.append((movimentacao, funcionario, produto))

    # Gráfico de produtos por mês/ano
    produtos_por_mes = produtos_por_mes_ano()  # Presumindo que essa função já existe
    meses, totais = zip(*[(resultado.mes_ano, resultado.total_produtos) for resultado in produtos_por_mes])

    return render_template('dashboard.html',
                           total_produtos=total_produtos,
                           total_funcionarios=total_funcionarios,
                           movimentacoes_recentes=movimentacoes_formatadas,
                           meses=meses,
                           totais=totais)


@app.route('/produto/grafico', methods=['GET', 'POST'])
def produto_grafico():
    resultados = produtos_por_mes_ano()
    meses, totais = zip(*[(resultado.mes_ano, resultado.total_produtos) for resultado in resultados])

    # Verifica se um tipo de gráfico foi selecionado
    tipo_grafico = request.args.get('tipo_grafico', 'bar')  # 'bar' é o padrão

    # Defina tamanhos maiores para os gráficos
    largura = 1400  # Define a largura desejada
    altura = 700  # Define a altura desejada

    # Gerar o gráfico com base no tipo selecionado
    if tipo_grafico == 'line':
        fig = px.line(x=meses, y=totais, labels={'x': 'Mês/Ano', 'y': 'Total de Produtos'},
                      title="Produtos por Mês/Ano", width=largura, height=altura)
    elif tipo_grafico == 'pie':
        fig = px.pie(names=meses, values=totais, title="Distribuição de Produtos por Mês/Ano",
                     width=largura, height=altura)
    elif tipo_grafico == 'scatter':
        fig = px.scatter(x=meses, y=totais, labels={'x': 'Mês/Ano', 'y': 'Total de Produtos'},
                         title="Dispersão de Produtos por Mês/Ano", width=largura, height=altura)
    elif tipo_grafico == 'area':
        fig = px.area(x=meses, y=totais, labels={'x': 'Mês/Ano', 'y': 'Total de Produtos'},
                      title="Área de Produtos por Mês/Ano", width=largura, height=altura)
    else:  # padrão para gráfico de barras
        fig = px.bar(x=meses, y=totais, labels={'x': 'Mês/Ano', 'y': 'Total de Produtos'},
                     title="Produtos por Mês/Ano", width=largura, height=altura)

    graph_json = pio.to_html(fig, full_html=False)
    return render_template('grafico_produtos.html', plot_html=graph_json)


@app.route('/funcionario', methods=['GET'])
def funcionario():
    por_pagina = 15
    pagina_atual = int(request.args.get('pagina', 1))
    ordem = request.args.get('ordem', 'id_funcionario_desc')

    # Calcular o offset
    offset = (pagina_atual - 1) * por_pagina

    # Determinar a ordem
    if ordem == 'nome_asc':
        order_by = Funcionario.nome_funcionario.asc()
    elif ordem == 'nome_desc':
        order_by = Funcionario.nome_funcionario.desc()
    elif ordem == 'id_funcionario_asc':
        order_by = Funcionario.id_funcionario.asc()
    else:  # padrão
        order_by = Funcionario.id_funcionario.desc()

    # Selecionar os produtos com limite e offset
    lista = (select(Funcionario).offset(offset).limit(por_pagina).order_by(order_by))
    lista = db_session.execute(lista).scalars().all()

    total_veterinarios = db_session.query(Funcionario).count()
    total_paginas = (total_veterinarios + por_pagina - 1) // por_pagina

    return render_template('funcionario.html',
                           cavalo=lista,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas,
                           ordem=ordem
                           )


@app.route('/novo_funcionario', methods=["POST", "GET"])
def novo_funcionario():
    if request.method == "POST":
        # Captura os valores dos campos do formulário
        nome_funcionario = request.form["form_nome_funcionario"]
        sobrenome = request.form["form_sobrenome_funcionario"]
        email = request.form["form_email_funcionario"]
        cpf = request.form["form_cpf_funcionario"]
        telefone = request.form["form_telefone_funcionario"]
        data_de_cadastro = datetime.now().strftime('%Y-%m-%d')

        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not nome_funcionario:
            erros.append("O campo 'Nome' é obrigatório.")
        if not sobrenome:
            erros.append("O campo 'Sobrenome' é obrigatório.")
        if not email:
            erros.append("O campo 'Email' é obrigatório.")
        if not cpf:
            erros.append("O campo 'CPF' é obrigatório.")
        if not telefone:
            erros.append("O campo 'Telefone' é obrigatório.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:
                # Se todos os campos estiverem preenchidos, cria o veterinário
                form_evento = Funcionario(
                    nome_funcionario=nome_funcionario,
                    sobrenome=sobrenome,
                    email=email,
                    cpf=cpf,
                    telefone=telefone,
                    data_de_cadastro=data_de_cadastro
                )
                form_evento.save()
                flash("Funcionario criado com sucesso!", "success")
                return redirect(url_for('funcionario'))
            except ValueError:
                flash("Ocorreu um erro ao criar o veterinário.", "error")

    return render_template('novo_funcionario.html')


@app.route('/editar_funcionario/<int:id_funcionario>', methods=["GET", "POST"])
def editar_funcionario(id_funcionario):
    funcionario = db_session.query(Funcionario).filter(Funcionario.id_funcionario == id_funcionario).first()
    if not funcionario:
        flash("Funcionário não encontrado.", "error")
        return redirect(url_for('funcionario'))

    if request.method == "POST":
        # Captura os valores dos campos do formulário
        nome_funcionario = request.form["form_nome_funcionario"]
        sobrenome = request.form["form_sobrenome_funcionario"]
        email = request.form["form_email_funcionario"]
        cpf = request.form["form_cpf_funcionario"]
        telefone = request.form["form_telefone_funcionario"]

        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not nome_funcionario:
            erros.append("O campo 'Nome' é obrigatório.")
        if not sobrenome:
            erros.append("O campo 'Sobrenome' é obrigatório.")
        if not email:
            erros.append("O campo 'Email' é obrigatório.")
        if not cpf:
            erros.append("O campo 'CPF' é obrigatório.")
        if not telefone:
            erros.append("O campo 'Telefone' é obrigatório.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:
                # Atualiza os dados do funcionário
                funcionario.nome_funcionario = nome_funcionario
                funcionario.sobrenome = sobrenome
                funcionario.email = email
                funcionario.cpf = cpf
                funcionario.telefone = telefone

                db_session.commit()
                flash("Funcionário atualizado com sucesso!", "success")
                return redirect(url_for('funcionario'))
            except ValueError:
                flash("Ocorreu um erro ao editar o funcionário.", "error")

    return render_template('editar_funcionario.html', funcionario=funcionario)


@app.route('/produto', methods=['GET'])
def produto():
    por_pagina = 10
    pagina_atual = int(request.args.get('pagina', 1))
    ordem = request.args.get('ordem', 'id_produto_desc')
    offset = (pagina_atual - 1) * por_pagina

    # Determinar a ordem
    if ordem == 'nome_asc':
        order_by = Produto.nome_produto.asc()
    elif ordem == 'nome_desc':
        order_by = Produto.nome_produto.desc()
    elif ordem == 'id_produto_asc':
        order_by = Produto.id_produto.asc()
    else:  # padrão
        order_by = Produto.id_produto.desc()

    # Selecionar os produtos com limite e offset
    lista = (select(Produto, Categoria)
             .join(Categoria, Categoria.id_categoria == Produto.id_categoria)
             .offset(offset).limit(por_pagina)
             .order_by(order_by))
    lista = db_session.execute(lista).fetchall()

    total_veterinarios = db_session.query(Produto).count()
    total_paginas = (total_veterinarios + por_pagina - 1) // por_pagina

    return render_template('produto.html',
                           cavalo=lista,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas,
                           ordem=ordem)


@app.route('/novo_produto', methods=["POST", "GET"])
def novo_produto():
    lista = db_session.execute(select(Categoria).order_by(Categoria.nome_categoria.asc())
                               ).scalars().all()
    if request.method == "POST":
        # Captura os valores dos campos do formulário
        nome_produto = request.form["form_nome_produto"]
        preco = request.form["form_preco_produto"]
        id_categoria = request.form["form_id_categoria"]
        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not nome_produto:
            erros.append("O campo 'Nome' é obrigatório.")
        if not preco:
            erros.append("O campo 'Preço' é obrigatório.")
        if not id_categoria:
            erros.append("O campo 'Categoria' é obrigatório.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:
                # força os valores a se converterem a float
                preco_float = float(preco)
                # força os valores a se converterem a int
                id_categoria_int = int(id_categoria)

                # Se todos os campos estiverem preenchidos, cria o produto
                form_evento = Produto(
                    nome_produto=nome_produto,
                    preco_produto=preco_float,
                    id_categoria=id_categoria_int
                )
                form_evento.save()
                flash("Produto criado com sucesso!", "success")
                return redirect(url_for('produto'))
            except ValueError:
                flash("Ocorreu um erro ao criar o Produto.", "error")

    return render_template('novo_produto.html', cavalo=lista)


@app.route('/editar_produto/<int:id_produto>', methods=["GET", "POST"])
def editar_produto(id_produto):
    produto = db_session.query(Produto).filter(Produto.id_produto == id_produto).first()
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('produto'))

    if request.method == "POST":
        # Captura os valores dos campos do formulário
        nome_produto = request.form["form_nome_produto"]
        preco_produto = request.form["form_preco_produto"]
        id_categoria = request.form["form_categoria_produto"]

        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not nome_produto:
            erros.append("O campo 'Nome do Produto' é obrigatório.")
        if not preco_produto:
            erros.append("O campo 'Preço' é obrigatório.")
        elif not preco_produto.replace('.', '', 1).isdigit():
            erros.append("O campo 'Preço' deve ser numérico.")
        if not id_categoria:
            erros.append("O campo 'Categoria' é obrigatório.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:
                # Atualiza os dados do produto
                produto.nome_produto = nome_produto
                produto.preco_produto = float(preco_produto)
                produto.id_categoria = int(id_categoria)

                db_session.commit()
                flash("Produto atualizado com sucesso!", "success")
                return redirect(url_for('produto'))
            except Exception as e:
                flash(f"Ocorreu um erro ao editar o produto: {str(e)}", "error")

    # Carregar todas as categorias para exibição no formulário
    categorias = db_session.query(Categoria).all()
    return render_template('editar_produto.html', produto=produto, categorias=categorias)


@app.route('/movimentacao', methods=['GET'])
def movimentacao():
    por_pagina = 10
    pagina_atual = int(request.args.get('pagina', 1))
    ordem = request.args.get('ordem', 'id_movimentacao_desc')
    offset = (pagina_atual - 1) * por_pagina

    # Determinar a ordem
    if ordem == 'nome_asc':
        order_by = Produto.nome_produto.asc()  # Verifique se isso está correto
    elif ordem == 'nome_desc':
        order_by = Produto.nome_produto.desc()
    elif ordem == 'id_movimentacao_asc':
        order_by = Movimentacao.id_movimentacao.asc()
    else:  # padrão
        order_by = Movimentacao.id_movimentacao.desc()

    # Selecionar as movimentações com limite e offset
    lista = (select(Movimentacao, Funcionario, Produto)
             .order_by(order_by)
             .join(Funcionario, Funcionario.id_funcionario == Movimentacao.id_funcionario)
             .join(Produto, Produto.id_produto == Movimentacao.id_produto)
             .offset(offset).limit(por_pagina))
    lista = db_session.execute(lista).fetchall()

    total_veterinarios = db_session.query(Movimentacao).count()
    total_paginas = (total_veterinarios + por_pagina - 1) // por_pagina

    return render_template('movimentacao.html',
                           cavalo=lista,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas,
                           ordem=ordem)


@app.route('/nova_movimentacao', methods=["POST", "GET"])
def nova_movimentacao():
    lista_funcionarios = db_session.execute(
        select(Funcionario).order_by(Funcionario.nome_funcionario.asc())
    ).scalars().all()

    lista_produtos = db_session.execute(
        select(Produto).order_by(Produto.nome_produto.asc())
    ).scalars().all()

    lista_movimentacao = db_session.execute(select(Movimentacao)).fetchall()

    if request.method == "POST":
        # Captura os valores dos campos do formulário
        id_funcionario = request.form["form_id_funcionario"]
        id_produto = request.form["form_id_produto"]
        quantidade = request.form["form_quantidade"]
        status = request.form["form_status"]
        data_movimentacao = datetime.now()

        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not status:
            erros.append("O campo 'Status' é obrigatório.")
        if not id_funcionario:
            erros.append("O campo 'Funcionário' é obrigatório.")
        if not id_produto:
            erros.append("O campo 'Produto' é obrigatório.")
        if not quantidade or not quantidade.isdigit():
            erros.append("O campo 'Quantidade' é obrigatório e deve ser um número.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:
                # Se todos os campos estiverem preenchidos, cria a movimentação
                form_evento = Movimentacao(
                    id_funcionario=int(id_funcionario),
                    id_produto=int(id_produto),
                    quantidade_produto=int(quantidade),
                    data_da_movimentacao=data_movimentacao,
                    status=status
                )
                form_evento.save()
                flash("Movimentação criada com sucesso!", "success")
                return redirect(url_for('movimentacao'))
            except ValueError:
                flash("Ocorreu um erro ao criar a movimentação.", "error")

    return render_template('nova_movimentacao.html',
                           funcionarios=lista_funcionarios,
                           produtos=lista_produtos,
                           movimentacoes=lista_movimentacao)


@app.route('/editar_movimentacao/<int:id_movimentacao>', methods=['GET', 'POST'])
def editar_movimentacao(id_movimentacao):
    lista_funcionarios = db_session.execute(select(Funcionario)).scalars().all()
    lista_produtos = db_session.execute(select(Produto)).scalars().all()
    movimentacao = db_session.query(Movimentacao).filter_by(id_movimentacao=id_movimentacao).first()

    if not movimentacao:
        flash("Movimentação não encontrada.", "error")
        return redirect(url_for('movimentacao'))

    if request.method == "POST":
        try:
            # Atualiza os dados da movimentação
            movimentacao.quantidade_produto = request.form["form_quantidade"]
            movimentacao.fornecedor = request.form["form_fornecedor"]
            movimentacao.status = request.form["form_status"]
            movimentacao.data_da_movimentacao = request.form["form_data_emissao"]
            movimentacao.id_funcionario = request.form["form_id_funcionario"]
            movimentacao.id_produto = request.form["form_id_produto"]

            db_session.commit()
            flash("Movimentação atualizada com sucesso!", "success")
            return redirect(url_for('movimentacao'))
        except Exception as e:
            db_session.rollback()
            flash(f"Erro ao atualizar a movimentação: {str(e)}", "error")

    # Renderiza o formulário com os dados existentes
    return render_template("editar_movimentacao.html",
                           movimentacao=movimentacao,
                           funcionarios=lista_funcionarios,
                           produtos=lista_produtos
                           )


@app.route('/categoria', methods=['GET'])
def categoria():
    por_pagina = 5
    pagina_atual = int(request.args.get('pagina', 1))
    ordem = request.args.get('ordem', 'id_categoria_desc')
    offset = (pagina_atual - 1) * por_pagina

    # Determinar a ordem
    if ordem == 'nome_asc':
        order_by = Categoria.nome_categoria.asc()
    elif ordem == 'nome_desc':
        order_by = Categoria.nome_categoria.desc()
    elif ordem == 'id_categoria_asc':
        order_by = Categoria.id_categoria.asc()
    else:  # padrão
        order_by = Categoria.id_categoria.desc()

    # Selecionar as categorias com limite e offset
    lista = (select(Categoria).order_by(order_by).offset(offset).limit(por_pagina))
    lista = db_session.execute(lista).scalars().all()

    total_categorias = db_session.query(Categoria).count()
    total_paginas = (total_categorias + por_pagina - 1) // por_pagina

    return render_template('categoria.html',
                           cavalo=lista,
                           pagina_atual=pagina_atual,
                           total_paginas=total_paginas,
                           ordem=ordem)


@app.route('/editar_categoria/<int:id_categoria>', methods=["GET", "POST"])
def editar_categoria(id_categoria):
    categoria = db_session.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if not categoria:
        flash("Categoria não encontrada.", "error")
        return redirect(url_for('categoria'))

    if request.method == "POST":
        # Captura os valores dos campos do formulário
        nome_categoria = request.form["form_nome_categoria"]

        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not nome_categoria:
            erros.append("O campo 'Nome da Categoria' é obrigatório.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:
                # Atualiza os dados da categoria
                categoria.nome_categoria = nome_categoria

                db_session.commit()
                flash("Categoria atualizada com sucesso!", "success")
                return redirect(url_for('categoria'))
            except Exception as e:
                flash(f"Ocorreu um erro ao editar a categoria: {str(e)}", "error")

    return render_template('editar_categoria.html', categoria=categoria)


@app.route('/nova_categoria', methods=["POST", "GET"])
def nova_categoria():
    lista = db_session.execute(select(Categoria).order_by(Categoria.nome_categoria.asc())
                               ).scalars().all()
    if request.method == "POST":
        # Captura os valores dos campos do formulário
        nome_categoria = request.form["form_nome_categoria"]
        # Lista para armazenar mensagens de erro
        erros = []

        # Validação de cada campo
        if not nome_categoria:
            erros.append("O campo 'Nome' é obrigatório.")

        # Se houver erros, exibe todas as mensagens
        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            try:

                # Se todos os campos estiverem preenchidos, cria o produto
                form_evento = Categoria(
                    nome_categoria=nome_categoria,
                )
                form_evento.save()
                flash("Categoria criada com sucesso!", "success")
                return redirect(url_for('categoria'))
            except ValueError:
                flash("Ocorreu um erro ao criar a Categoria.", "error")

    return render_template('nova_categoria.html', cavalo=lista)


if __name__ == '__main__':
    app.run(debug=True)
