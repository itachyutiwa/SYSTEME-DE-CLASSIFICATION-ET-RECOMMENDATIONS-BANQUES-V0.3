from flask import Flask, render_template, session, redirect, request
from functools import wraps
import pymongo
import config
import services.statistiques_et_kpi as statistiques_et_kpi
import services.database_connexion as database_connexion 
import generate_graphics as generate_graphics
import random


app = Flask(__name__)
app.secret_key = b'\xcc^\x91\xea\x17-\xd0W\x03\xa7\xf8J0\xac8\xc5'

# Database
#Récupération des variables d'environnement
cluster =config.environ['CLUSTER']
username =config.environ['USERNAME']
dbname =config.environ['DBNAME']
password =config.environ['PASSWORD']

# Connexion à la base de données MongoDB
client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@{cluster}.rnawsej.mongodb.net/")

# Spécifiez la base de données que vous souhaitez utiliser
db = client[f"{dbname}"]
db = client.user_login_system

def generate_random_ids(prefix, n):
    ids = []
    for _ in range(n):
        random_number = random.randint(0, 9999999)
        id_with_prefix = f"{prefix}{random_number:07}"
        ids.append(id_with_prefix)
    return ids

  # Remplacez par le préfixe souhaité

# Decorators
def login_required(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      return redirect('/')
  
  return wrap

# Routes
from user import routes

@app.route('/')
def home():
  context = {"title":"Connexion"}
  return render_template('home.html', context=context)

@app.route('/user/signup')
def register():
  context = {"title":"Inscription"}
  return render_template('signup.html', context=context)

@app.route('/dashboard/')
@login_required
def dashboard():
  df = database_connexion.data_copy
  # Chargement des données
  data = df.copy()
  # Calcul du solde moyen quotidien (ADB)
  data['ADB'] = data['BALANCE'] / data['TENURE']

  # Calcul du montant total des achats
  data['TOTAL_PURCHASES'] = data['ONEOFF_PURCHASES'] + data['INSTALLMENTS_PURCHASES']

  context = {
    "balance_mean":statistiques_et_kpi.balance_mean(data),
    "purchases_freq_mean":statistiques_et_kpi.purchases_freq_mean(data),
    "purchases_trx_sum":statistiques_et_kpi.purchases_trx_sum(data),
    "payments_mean":statistiques_et_kpi.payments_mean(data),
    "title": "Tableau de bord"
    }
  fig_hist = generate_graphics.hist_solde_compte(data)
  graph_html_hist = fig_hist.to_html(full_html=False)

  fig_pie = generate_graphics.pie_ratio_achats_ponctuels(data)
  graph_html_pie = fig_pie.to_html(full_html=False)

  fig_barr = generate_graphics.barr_transaction_par_grp_client(data)
  graph_html_barr = fig_barr.to_html(full_html=False)

  fig_nuage = generate_graphics.nuage_de_points_montant_total_des_achats(data)
  graph_html_nuage = fig_nuage.to_html(full_html=False)

  graphiques = {
     #Affichage de l'histogramme du solde des comptes dans le
        "hist_solde_compte":graph_html_hist,

        # Affichage du graphique du ratio d'achats ponctuels dans le dashboard
        "pie_ratio_achats_ponctuels":graph_html_pie,

        # Création du graphique en barres groupées pour le nombre de transactions par groupe de clients
        "barr_transaction_par_grp_client":graph_html_barr,

        # Tracer un nuage de points du montant total des achats par rapport à l'ADB
        "nuage_de_points_montant_total_des_achats":graph_html_nuage
  }
  return render_template('index.html',context=context, graphiques = graphiques)


@app.route('/profil/')
@login_required
def profil():
  return render_template('dashboard.html')

@app.route('/marketing/')
@login_required
def marketing():
  df = database_connexion.data_copy
  # Chargement des données
  data = df.copy()
  context = {
    "balance_mean":statistiques_et_kpi.balance_mean(data),
    "purchases_freq_mean":statistiques_et_kpi.purchases_freq_mean(data),
    "purchases_trx_sum":statistiques_et_kpi.purchases_trx_sum(data),
    "payments_mean":statistiques_et_kpi.payments_mean(data),
    "title":"Marketing clients"
    }
  
  return render_template('marketing.html', context=context)

@app.route('/segments/', methods=['POST', 'GET'])
@login_required
def segments():
  df = database_connexion.data_copy
  # Chargement des données
  random.seed(1232)
  data = df.copy()
  context = {
    "balance_mean":statistiques_et_kpi.balance_mean(data),
    "purchases_freq_mean":statistiques_et_kpi.purchases_freq_mean(data),
    "purchases_trx_sum":statistiques_et_kpi.purchases_trx_sum(data),
    "payments_mean":statistiques_et_kpi.payments_mean(data),
    "title":"Segments clients"
    
    }
  
  sample_size = data.shape[0]  # Remplacez par la taille d'échantillon souhaitée
  prefix = "XXXX_"
  ID = []
  random_ids = generate_random_ids(prefix, sample_size)
  for i in random_ids:
    ID.append(i)
  data["CUST_ID"] = ID

  #data = data[data["cluster_result"] == request.form.get('cluster')]
  #cluster = request.form.get('cluster')
  data = data[data["cluster_result"] == request.form.get('cluster') ]
  data = data.head(10)
  data_list = data.to_dict('records')

  return render_template('segments.html', context=context, data=data_list)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)