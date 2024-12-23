import random
from faker import Faker
from models import db_session, Funcionario, Produto, Categoria, Movimentacao, init_db

# Configuração para dados em português
fake = Faker('pt_BR')

def create_fake_funcionarios(num):
    for _ in range(num):
        funcionario = Funcionario(
            nome_funcionario=fake.first_name(),
            sobrenome=fake.last_name(),
            email=fake.unique.email(),
            cpf=fake.unique.random_int(min=10000000000, max=99999999999),
            telefone=fake.phone_number(),
            data_de_cadastro=fake.date_this_decade().isoformat()
        )
        funcionario.save()
    db_session.commit()  # Salvar todos os funcionários no banco

def create_fake_categorias():
    categorias = [
        'Eletrônicos', 'Alimentos', 'Roupas', 'Móveis', 'Livros',
        'Ferramentas', 'Brinquedos', 'Cosméticos', 'Esporte',
        'Jardinagem', 'Veículos', 'Informática', 'Bebidas',
        'Utensílios Domésticos', 'Material Escolar'
    ]
    for nome_categoria in categorias:
        categoria = Categoria(nome_categoria=nome_categoria)
        categoria.save()
    db_session.commit()  # Salvar todas as categorias no banco

def create_fake_produtos():
    categoria_produto_map = {
        'Eletrônicos': [('Smartphone', 500, 3000), ('Notebook', 1000, 5000), ('Televisão', 800, 4000)],
        'Alimentos': [('Cerveja', 5, 20), ('Refrigerante', 3, 10)],
        'Roupas': [('Camiseta', 20, 100)],
        'Móveis': [('Sofá', 300, 2000), ('Geladeira', 1000, 3000), ('Fogão', 300, 1500)],
        'Livros': [('Livro', 20, 150)],
        'Ferramentas': [('Chave Inglesa', 10, 50)],
        'Brinquedos': [('Boneca', 20, 150), ('Brinquedo de Montar', 30, 200)],
        'Cosméticos': [('Shampoo', 10, 50)],
        'Esporte': [('Bola de Futebol', 50, 200)],
        'Jardinagem': [('Regador', 15, 100)],
        'Veículos': [('Carro', 15000, 50000), ('Motocicleta', 5000, 20000)],
        'Informática': [('Mouse', 20, 150), ('Teclado', 50, 300)],
        'Bebidas': [('Cerveja', 5, 15), ('Refrigerante', 3, 8)],
        'Utensílios Domésticos': [('Cafeteira', 50, 300)],
        'Material Escolar': [('Tesoura', 5, 20)]
    }

    categorias = db_session.query(Categoria).all()
    categoria_ids = {categoria.nome_categoria: categoria.id_categoria for categoria in categorias}

    for categoria, produtos in categoria_produto_map.items():
        for nome_produto, preco_min, preco_max in produtos:
            produto = Produto(
                nome_produto=nome_produto,
                preco_produto=round(random.uniform(preco_min, preco_max), 2),
                qtd=random.randint(10, 100),  # Quantidade inicial de produtos
                id_categoria=categoria_ids[categoria]
            )
            produto.save()
    db_session.commit()  # Salvar todos os produtos no banco

def create_fake_movimentacoes(num, funcionario_ids, produto_ids):
    # Consulta os produtos para atualizar a quantidade
    produtos_map = {produto.id_produto: produto for produto in db_session.query(Produto).all()}

    for _ in range(num):
        id_produto = random.choice(produto_ids)
        quantidade = random.randint(1, 100)
        status = random.choice(['Entrada', 'Saída'])

        # Atualiza a quantidade de produtos com base na movimentação
        if status == 'Entrada':
            produtos_map[id_produto].qtd += quantidade
        elif status == 'Saída' and produtos_map[id_produto].qtd >= quantidade:
            produtos_map[id_produto].qtd -= quantidade
        else:
            # Evita movimentações de saída que resultem em quantidade negativa
            continue

        movimentacao = Movimentacao(
            quantidade_produto=quantidade,
            fornecedor=fake.company(),
            status=status,
            data_da_movimentacao=fake.date_this_decade(),
            id_funcionario=random.choice(funcionario_ids),
            id_produto=id_produto
        )
        movimentacao.save()

    # Salva as atualizações no banco
    db_session.commit()

def main():
    init_db()

    # Criando dados fictícios
    create_fake_funcionarios(50)
    funcionarios = db_session.query(Funcionario).all()
    funcionario_ids = [f.id_funcionario for f in funcionarios]

    create_fake_categorias()
    categorias = db_session.query(Categoria).all()
    categoria_ids = [c.id_categoria for c in categorias]

    create_fake_produtos()
    produtos = db_session.query(Produto).all()
    produto_ids = [p.id_produto for p in produtos]

    create_fake_movimentacoes(len(produto_ids), funcionario_ids, produto_ids)

    print("Banco de dados populado com dados fictícios.")

if __name__ == '__main__':
    main()
