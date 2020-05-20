# Queenbee :crown:

Queenbee is a workflow language for describing workflows! The workflow Schema
is inspired by [Argo Workflow](https://argoproj.github.io/docs/argo/readme.html) and
borrows a number of terms and expressions from
[Apache Airflow](http://airflow.apache.org/) and [Ansible](https://docs.ansible.com/).

Queenbee populates and validates the workflows but does not run them! For running the
workflows see
[`ladybug-tools/queenbee-luigi`](https://github.com/ladybug-tools/queenbee-luigi)
which converts Queenbee workflows to executable
[Luigi](https://luigi.readthedocs.io/en/stable/) pipelines.

You can find more workflow samples in
[honeybee-radiance-workflow](https://github.com/ladybug-tools/honeybee-radiance-workflow)
repository.


## Installation

```
> pip install queenbee
```

or if you want to use the CLI
```
> pip install queenbee[cli]
```


## Documentation

You can access the full docs for this package and its CLI [here](https://ladybug.tools/queenbee).

You can also access the [Schema Documentation](https://ladybug.tools/queenbee/redoc.html) and [raw OpenAPI definitions](https://ladybug.tools/queenbee/openapi.json).

## Local Development

1. Clone this repo locally

    ```console
    git clone git@github.com:ladybug-tools/queenbee
    ```

    or

    ```console
    git clone https://github.com/ladybug-tools/queenbee
    ```

2. Install dependencies:

    ```console
    cd queenbee
    pip install -r dev-requirements.txt
    pip install -r requirements.txt
    ```

3. Run Tests:

    ```console
    python -m pytest tests/
    ```

4. Generate Documentation:

    ```python
    sphinx-apidoc -f -e -d 4 -o ./docs/modules ./queenbee
    sphinx-build -b html ./docs ./docs/_build
    ```

5. Preview Documentation:

    ```console
    python -m http.server --directory ./docs/_build/
    ```

    Now you can see the documentation preview at http://localhost:8000
