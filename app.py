from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

entries = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        website = request.form['website']
        username = request.form['username']
        password = request.form['password']
        entries.append({
            'website': website,
            'username': username,
            'password': password
        })
        return redirect(url_for('index'))
    return render_template('index.html', entries=entries)

if __name__ == '__main__':
    app.run(debug=True) 