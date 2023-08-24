> This container has a default run command that will automatically start the Jupyter Lab.

## Necessary work-around

Once starting the `jupyter_clickable_image_widget` container, kill Jupyter Lab process, and install everything again, then start Jupyter Lab server again.

```
ps
kill 24 # kill the process that is executing `jupyter lab`
python3 -m pip install git+https://github.com/ipython/traitlets@main
curl -fsSL https://deb.nodesource.com/setup_16.x | bash - 
apt-get update && \
    apt-get install -y --no-install-recommends \
            libssl-dev \
            nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean
jupyter labextension install @jupyter-widgets/jupyterlab-manager
cd /jupyter_clickable_image_widget
git checkout tags/v0.1
pip3 install -e .
jupyter labextension install js
jupyter lab build
jupyter lab --ip 0.0.0.0 --port 8888 --allow-root
```

Then open a new Jupyter notebook, and run the following code.

```
from jupyter_clickable_image_widget import ClickableImageWidget
```