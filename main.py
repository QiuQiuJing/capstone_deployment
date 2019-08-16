import flask
from flask import Flask, jsonify 
import pandas as pd
from html.parser import HTMLParser


app = Flask(__name__)
app.config['DEBUG'] = True

app.static_folder = 'templates/static'

#-------- DATA -----------#
df = pd.read_csv('../datasets/product_info_clean.csv')
content = pd.read_csv('../datasets/content_sim.csv')
collab = pd.read_csv('../datasets/collaborative_sim.csv')
repurchase = pd.read_csv('../datasets/repurchase.csv')

#drop Unnamed: 0 columns
df.drop(columns = 'Unnamed: 0', axis = 1, inplace = True)
collab.drop(columns = 'id', axis =1 , inplace =True)
content.drop(columns = 'Unnamed: 0', axis = 1, inplace = True)
repurchase.drop(columns = 'Unnamed: 0', axis = 1, inplace = True)

#-------- ROUTES -----------#
@app.route('/home')
def main_input():
    return flask.render_template('input_page.html')

@app.route('/product', methods=['POST', 'GET'])
def get_cat():
    if flask.request.method == 'POST':
        cat = flask.request.values.get("cat_in")
        product_name = flask.request.values.get("product_name")
    
        product_id = df[df.full_name == product_name].index[0]
    
        #index of products from desired category
        cat_in = df[df.Category == cat].index

        #rank product by similarity, lower the ranking number, higher the similarity
        content_rank = content.iloc[product_id,cat_in].rank(ascending=False, method='min')
        collab_rank = collab.iloc[product_id,cat_in].rank(ascending=False, method='min')

        #aggregate two rankings to get overall rankings
        rank = content_rank + collab_rank

        #sort rankings with ascending orders, products on top will most likely be recommended
        rank = rank.sort_values()[1:]

        #for products have same rankings after aggragation, we will take into account the repurchase rate.
        re_one = rank[rank.duplicated()]
        re_all = rank[rank.duplicated(keep=False)]
        
        for i in re_one:
            list_index = []
            list_num = []
            for e in re_all.index:
                if i == re_all[e]:
                    list_index.append(e)
                    list_num.append(int(e))
            r = repurchase.loc[list_num,'rate'].rank(ascending = False,method = 'min')
            rank[list_index] = rank[list_index] + list(0.01*r)   
        rank_sum = pd.DataFrame({'content_rank':content_rank, 'collab_rank':collab_rank , 'rank':rank})    
        #show the top 10 products' infomation  
        result = df.iloc[list(rank.sort_values()[:10].index)]

        #show cosine similarity score for both content base and collaborative
        content_sim = list(content.iloc[product_id,list(result.index)])
        collab_sim = list(collab.iloc[product_id,list(result.index)])
        content_rank = [int(i) for i in list(rank_sum.loc[list(map(str, result.index)),'content_rank'])]
        collab_rank = [int(i) for i in list(rank_sum.loc[list(map(str, result.index)),'collab_rank'])]
        brand = [i for i in result.brand]
        name = [i for i in result.name]
        pic = [i for i in result.pic]
        url = [i for i in result.URL]
       # result['content_sim'] = content_sim
        #result['collab_sim'] = collab_sim
        #final_dic = {'3.collaborative':collab_sim, '2.content based': content_sim, '1.product name': list(result["full_name"])}
        
        return flask.render_template('output_page.html',url=url, brand=brand, name = name, pic = pic, content_rank =content_rank, collab_rank = collab_rank)
    
   






if __name__ == '__main__':
    app.run()
