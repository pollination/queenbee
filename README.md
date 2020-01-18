# queenbee

:crown: Queenbee is a workflow language for creating workflows! The Queenbee workflow
is inspired by [Argo Workflow](https://argoproj.github.io/docs/argo/readme.html) and
borrows a number of terms and expressions from
[Apache Airflow](http://airflow.apache.org/) and [Ansible](https://docs.ansible.com/).

Queenbee populates and validates the workflows but does not run them! For running the
workflows see `ladybug-tools/workerbee` which converts Queenbee workflows to executable
[Luigi](https://luigi.readthedocs.io/en/stable/) pipelines.

You can find more workflow samples in
[honeybee-radiance-workflow](https://github.com/ladybug-tools/honeybee-radiance-workflow)
repository.

# Queenbee Workflow structure

A Queenbee workflow is a YAML / JSON file which consists of different parts. You
can use Queenbee to generate the workflows programmatically using Python or you can
write a workflow line by line.

Here we discuss the generic structure of a Queenbee workflow. [See OpenApi schema
documentation for all Workflow objects](https://www.ladybug.tools/queenbee/).

```
  Workflow
    |
    |__ name
    |
    |__ artifact_locations
    |
    |__ inputs
    |   |___ parameters
    |   |___ artifacts
    |
    |__ operators
    |
    |__ templates
    |
    |__ flow
    |   |___ tasks / steps
    |
    |__ outputs
        |___ parameters
        |___ artifacts

```

## 1. Artifact Locations

Artifacts are files that will be used during different steps of the workflow computation.
These files can be stored on different types of systems (remote folder, local machine or
API call to a webapp). Every artifact indicates which `location` or source-system it is
to be acquired from, and each `Artifact Location` is listed in the `artifact_locations`
key of the `workflow` object. Currently 3 types of locations are supported:

* **Local**: Artifacts situated on the machine running the workflows
* **HTTP**: Artifacts that can be sourced from a website or web API
* **S3**: Artifacts that can be retrieved from an S3 bucket

```yaml
artifact_locations:
- name: local-test
  type: local
  root: C:\Users\Test\Projects\Project 1

- name: http-test
  type: http
  root: http://climate.onebuilding.org
  headers: 
    Authorization: some-long-JWT-token

- name: s3-test
  type: s3
  root: pollination
  endpoint: s3.eu-west-1.amazonaws.com
  bucket: all-of-my-data
  credentials_path: C:\Users\Test\.queenbee\config.yaml
```

## 2. inputs

Workflow inputs are global inputs that can be accessed as `"{{workflow.inputs.xx.yy}}"`
when creating the `flow` section. For instance to access an input parameter with the
name `file-path` one should use `"{{workflow.inputs.parameters.file-path}}"` and Queenbee
will map the value of `file-path` parameter to this place-holder.

Inputs can be from two different types: `parameters` and `artifacts`.

Input `artifacts` are a collection of *files* that will be accessed during the run.
Artifacts in this section usually exist before the execution of the workflow. If the
`artifact` is generated as part of the `flow` it is usually identified in that `step` of
the `flow`. Keep in mind that in distributed execution that each section of the `flow`
might be executed on a separate machine the content of these `artifacts` will be copied
to target location before executing the workflow. For all the other `inputs` use
`parameters`.

Here is an example `inputs` for a typical simulation workflow. The `parameters` section
is used to define the maximum number of workers during the execution of the workflow and
`artifacts` section is used to define the project-folder. Both inputs have a default
value which can be overwritten by an input file.


```yaml

  inputs:
    parameters:
    - name: worker
      description: Maximum number of workers for executing this workflow.
      value: 1   # this is the default value which can be overwritten
    artifacts:
    - name: model-folder
      description: |
        Path to project folder for this study. This will make it easy to use relative
        path for other template inputs.
      location: project-folder
      path: models/
      task_path: . # this is the default value which can be overwritten

```

## 3. operators

`Operators` include the requirements for running `templates` [see below]. In a valid
workflow all the the `operators` that are referenced by `templates` should be included
in this section. Keep in mind that the operators are reusable and can be shared between
different templates. The `image` field identifies the Docker image for running a
`template`. Below is an operator for running arbitrary Radiance commands.

```yaml
  - name: radiance-operator
    image: ladybugtools/radiance:5.2
```

Here is another operator example for running `honeybee-radiance` commands.

```yaml

  - name: honeybee-radiance
    image: ladybugtools/honeybee-radiance:latest

```

You can also import the operator from a `YAML` or `JSON` file using the `import_from`
key. All the fields will be loaded from the file except for the `name`. The original name
will be kept since this is the name that has been used inside the workflow to refer to
this operator.

```yaml

operators:
  - name: radiance-operator  # will NOT change based on the operator name in the file
    import_from: 'radiance_operator.yaml'  # relative path to the workflow file itself

```

In this example the content of `radiance_operator.yaml` can be something like this:

```yaml
---
name: honeybee-radiance
image: ladybugtools/honeybee-radiance:latest

```

## 4. templates

Templates are discrete reusable units of code that can be executed separately or as part
of a workflow. Queenbee supports 4 types of objects as templates:

- `function` : A single function to execute a single command.
- `dag`: Collection of functions as a Directed Acyclic Graph (DAG).
- `workflow`: A full Queenbee workflow itself can be referenced as a template in another
  workflow.

Templates can use the `import_from` keyword to import the `template` from a `YAML` or
`JSON` file. Keep in mind that a template in a file should be self-sufficient and include
all the information including `operator`s. This is different from when the `template` is
part of the `workflow` where an `operator` will be referenced by name.

Here is an example `function` for generating a sky with desired irradiance which is part
of a workflow. In order to make it a valid `template` in a separate file you should use
the full operator specification from the last step instead of only using the name of the
operator.

```yaml
  name: generate-overcast-sky
  type: function
  inputs:
    parameters:
      - name: desired-irradiance
        description: desired sky horizontal irradiance
      - name: sky-file
        description: full path to output sky file
  operator: radiance-operator
  # commands and args will be used both locally and inside the container
  # TODO: This must change to be platform specific
  command: gensky -c -B "{{inputs.parameters.desired-irradiance}}" > file.sky
  outputs:
    artifacts:
      - name: sky
        task_path: file.sky
        path: "{{inputs.parameters.sky-file}}"
        source: project-folder
```

## 5. flow

`flow` is the workflow logic that defines in what order the templates should be executed
and how the output from one task will be consumed by another task(s). Such a workflow is
also known as Directed Acyclic Graph (DAG).

Here is an example of creating a sky and generating an octree as two consecutive steps.

```yaml

flow:
  - name: prepare-sky-and-octree
    tasks:
      - name: generate-sky-step
        template: generate-sky
        inputs:
          parameters:
            - name: desired_irradiance
              value: 100000
      - name: generate_octree_step
        template: generate_octree
        dependencies: [generate-sky]
        inputs:
          parameters:
            - name: scene_files
              value: |
                "{{tasks.generate_sky_steps.outputs.sky_file}}"
                "{{workflow.inputs.parameters.folder}}"/model/static/scene.mat
                "{{workflow.inputs.parameters.folder}}"/model/static/scene.rad

```

Now let's think about a longer workflow which also includes ray-tracing using the
generated octree. We need to add two new steps to the workflow:

1. generate sensor grids
2. run ray-tracing

But there is a difference between these new two steps and the initial two steps.
In the first two steps the second step of generating the octree was dependant on the
first step and it couldn't be executed until generating sky is finished. However for
generating the sensor grids we we do not need to wait for generating sky to be finished.
Finally, the last step of ray-tracing will need both the grid and the octree.

To describe such flows we will use a Directed Acyclic Graph or DAG. Here
is the updated process.

Also since the step for generating grids can generate more than one grid we are using
loop to run ray-tracing for all these grids in parallel.

```

                              sky    grids
                                |      |
                              octree   |
                                |      |
                                \______/
                                    |
                                ray-tracing
                         ___________|_____________
                        /       |       |         \
                      g-1-1   g-1-2   g-2-1 ... g-n-m
                        \_______|_______|_________/
                                    |
                              collect results

```

```yaml

flow:
  - name: sample-workflow
  - tasks:
    - name: generate_sky_task
      template: generate_sky
      inputs:
        parameters:
          - name: desired_irradiance
            value: 100000
    - name: generate_octree_task
      template: generate_octree
      dependencies:
        - generate_sky_task
      inputs:
        parameters:
           - name: scene_files
             value: |
               "{{tasks.generate_sky_steps.outputs.sky_file}}"
               "{{workflow.inputs.parameters.folder}}"/model/static/scene.mat
               "{{workflow.inputs.parameters.folder}}"/model/static/scene.rad
    - name: generate_grids_task
      template: generate_grids
      inputs:
        parameters:
          - name: max_sensor_count
            value: 200
    - name: ray_tracing_task
      template: run_raytracing
      dependencies:
        - generate_octree_task
        - generate_grids_task
      inputs:
        parameters:
          - name: grid
            value: "{{item}}"
          - name: octree
            value: "{{tasks.generate_octree_task.outputs.parameters.octree}}"
      loop: "{{ tasks.generate_grids_task.outputs.parameters.grids }}"
```

## 6. outputs

Several files might be generated in the `process` section and the `outputs` `artifacts`
section indicates which ones should be saved as the final outputs of the `workflow`.
Executors may return these outputs as a collection of file locations or file contents.

Outputs can also return `parameters` that are generated in the `process` section of the
workflow. 


## Variables

As you can see it is common to use the output of one task as an input for another task or
reference one of the workflow inputs as an input for one of the steps or tasks. Queenbee
supports the following words as prefix variable names:

### Global variables

| Variable | Description|
|----------|------------|
| `workflow.name` | Replaced by workflow name |
| `workflow.id` | Replaced by workflow id |
| `workflow.inputs.parameters.<NAME>` | Replaced by `value` for parameter `<NAME>` |
| `workflow.inputs.artifacts.<NAME>` | Replaced by `path` for artifact `<NAME>` |
| `workflow.operators.<OPERATORNAME>.image` | Replaced by image name for operator `<OPERATORNAME>` |

### Flow variables

| Variable | Description|
|----------|------------|
| `tasks.<TASKNAME>.outputs.parameters.<NAME>` | Output parameter of any previous task |
| `tasks.<TASKNAME>.outputs.artifacts.<NAME>` | Output artifact of any previous task |

### Task variables

| Variable | Description|
|----------|------------|
| `inputs.parameters.<NAME>` | Input parameter of task `<NAME>`|
| `inputs.artifacts.<NAME>` | Input artifact of task `<NAME>`|
| `outputs.parameters.<NAME>` | Output parameter of task `<NAME>`|
| `outputs.artifacts.<NAME>` | Output artifact of task `<NAME>`|

### Loops

| Variable | Description|
|----------|------------|
| `item` | Replaced by the value of item |
| `item.<FIELDNAME>` | Replaced by the field value of the item |


# TODO: Command Line Interface

You can also use queenbee from command line. The most commonly used commands are:

## validate

`queenbee validate [WORKFLOW-FILE]`

This command validates the workflow to ensure:
  a. the workflow complies with queenbee schema
  b. all the `import_from` resources are available and valid.
  c. all the operators are included in workflow file.

You can also validate a workflow against an input file.

`queenbee validate [WORKFLOW-FILE] --inputs [INPUT-FILE]`

## package

`queenbee package [WORKFLOW-FILE] [PACKAGED-WORKFLOW-FILE]`

This command packages the workflow and all its dependencies into a single file. If
there is no `import_from` in original workflow the packaged workflow will be identical
to the original workflow.

## freeze

`queenbee freeze [WORKFLOW-FILE] [INPUT-FILE] [FROZEN-WORKFLOW-FILE]`

Queenbee workflows are designed to be reusable and it is valid to have input parameters
with no default values. These values will be provided in an input file. In some cases
you want to use the workflow over and over with the same input values. This command
makes a frozen version of the workflow with all the values hard-coded in the workflow.

`freeze` command calls `package` command under the hood. In other words a frozen
workflow will not have an `import_from` key.

## populate-inputs

`queenbee populate-inputs [WORKFLOW-FILE] [INPUT-FILE]`

This command generates a template input file for a specific workflow. You can use
`--include-defaults` flag to also get the inputs that already have a default value. The
inputs with referenced inputs with prefix variable name (e.g.
"{{tasks.create_octree.outputs.artifacts.octree}}") will not be included in the inputs
file. 

## visualize

`queenbee visualize [WORKFLOW-FILE]`

This command creates an interactive visual representation of the workflow.

![image](https://user-images.githubusercontent.com/2915573/61600213-9405e280-abfd-11e9-91e7-a0a622ca3ece.png)
