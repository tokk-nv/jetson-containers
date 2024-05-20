# make a samples variant of the container
samples = package.copy()

samples['name'] = 'llama-index:samples'
samples['dockerfile'] = 'Dockerfile.samples'
samples['depends'] = ['llama-index:main', 'jupyterlab:myst', 'ollama']

del samples['alias']

streamlit = package.copy()

streamlit['name'] = 'llama-index:streamlit'
streamlit['dockerfile'] = 'Dockerfile.streamlit'
streamlit['depends'] = ['llama-index:main', 'ollama']

del streamlit['alias']

package = [package, samples, streamlit]