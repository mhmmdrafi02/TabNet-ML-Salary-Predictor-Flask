# Import library yang diperlukan
from datetime import datetime
import io
from io import StringIO
import numpy as np
import pandas as pd
from pytorch_tabnet.tab_model import TabNetClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from flask import Flask, request, render_template

# Inisialisasi Flask app dan memuat model TabNet yang sudah dilatih
app = Flask(__name__)
loaded_model = TabNetClassifier()
loaded_model.load_model('tabnet_model.zip')

# Fungsi untuk melakukan feature engineering pada dataframe
def feature_engineering(df):
    df.columns = ['age', 'workclass', 'education', 'education_num', 'marital_status', 'occupation', 'relationship', 'race',
                  'sex', 'capital_gain', 'capital_loss', 'hours_per_week', 'income_>50K']
    
    df = df.drop('income_>50K', axis=1)

    label_encoder = LabelEncoder()

    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = label_encoder.fit_transform(df[column])
    
    return df

# Fungsi untuk melakukan standard scaling pada dataframe
def scalar(df):
    sc = StandardScaler()
    X =  df[['age', 'workclass', 'education', 'education_num', 'marital_status', 'occupation', 'relationship', 
            'race', 'sex', 'capital_gain', 'capital_loss', 'hours_per_week']]
    X = sc.fit_transform(X)

    return X

# Route untuk halaman utama
@app.route('/', methods=['GET'])
def Home():
    return render_template('index.html')

# Route untuk melakukan prediksi pada data yang diunggah
@app.route('/predict', methods=['POST'])
def predict():
    # Menghitung waktu eksekusi prediksi
    start_time = datetime.now()

    # Menerima file CSV yang diunggah
    f = request.files['data_file']
    if not f:
        return render_template('index.html', prediction_text="No file selected")
    
    # Membaca file CSV dan melakukan feature engineering
    stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
    result = stream.read()
    df = pd.read_csv(StringIO(result))
    dfx = feature_engineering(df)

    # Melakukan standard scaling
    X = scalar(dfx)

    # Melakukan prediksi dengan model TabNet
    result = loaded_model.predict(X)

    # Menghitung waktu eksekusi prediksi
    end_time = datetime.now()
    prediction_time = (end_time - start_time).total_seconds()

    # Mengubah hasil prediksi menjadi label '>50k' atau '<=50k'
    result_labels = np.where(result == 1, '>50k', '<=50k')

    # Menambah kolom hasil prediksi pada dataframe
    df['Predicted_Label'] = result_labels
    
    # Menghitung akurasi prediksi
    ground_truth = df['income_>50K'].values
    accuracy = accuracy_score(ground_truth, result)

    # Menampilkan hasil prediksi dan akurasi pada halaman web
    return render_template('index.html', 
                            prediction_text="Predicted Salary is/are: {}".format(result_labels),
                           time_text="Prediction Time: {:.4f} seconds".format(prediction_time),
                           accuracy_text="Accuracy: {:.2%}".format(accuracy),
                           df_table=df.to_html())

# Menjalankan aplikasi Flask
if __name__ == "__main__":
        app.run(debug=True, host='0.0.0.0', port=2000)
