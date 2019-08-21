# queenbee

👑 Queenbee is a workflow language for creating complex workflows! The Queenbee workflow
is inspired by [Argo Workflow](https://argoproj.github.io/docs/argo/readme.html) and
borrows a number of terms and expressions from
[Apache Airflow](http://airflow.apache.org/) and [Ansible](https://docs.ansible.com/).

Queenbee populates and validates the workflows but does not run them. For running the
workflows see `ladybug-tools/workerbee` which converts Queenbee workflows to executable
[Luigi](https://luigi.readthedocs.io/en/stable/) workflows.

You can find more workflow samples in
[honeybee-radiance-workflow](https://github.com/ladybug-tools/honeybee-radiance-workflow)
repository. The workflow is meant to mainly be used with Ladybug Tools libraries but it
should also support any other custom workflows.

# Queenbee Workflow structure

A Queenbee workflow is a YAML / JSON file which consists of different parts. You
can use Queenbee to generate the workflows programmatically using Python or you can
write a workflow line by line.

Here we discuss the generic structure of a Queenbee workflow. See OpenApi schema
documentation for all Workflow objects: [Missing link]()

```

  Workflow
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

## 1. inputs

Workflow inputs are global inputs that can be accessed using `"{{workflow.inputs.xx.yy}}"`.
For instance to access an input parameter with the name `file_path` one should use
`"{{workflow.inputs.parameters.file_path}}"` and Queenbee will map the value of
`file_path` parameter to this placeholder.

Inputs can be from two different types: `parameters` and `artifacts`. Use `artifacts` for
*files* and *folder* inputs. The content of these `artifacts` will be copied to target
location before executing the workflow. For all the other `inputs` use `parameters`.

Here is an example `inputs` for a daylight simulation workflow. You can put a default
value for inputs or it can be passed to workflow using an input YAML / JSON file.

```yaml

  inputs:
    parameters:
    # this is just the path to target folder not the content itself. It can be referenced
    # as {{workflow.parameters.folder}}
    - name: folder
      value: /mnt/c/ladybug/untitled
    artifacts:
    - name: sky_file
      path: full_path_to_sky_file.sky
    - name: material_file
      path: full_path_to_material_file.mat
    - name: geometry_file
      path: full_path_to_geometry_file.rad

```

## 2. operators

`Operators` include the requirements for running `templates` locally or using a Docker
image. Operators are referenced from inside `templates` [see below]. To have a valid
workflow all the `operators` that are referenced by `templates` must be included in this
section.

An operator has two separate sections for `container` and `local`. Container identifies
the Docker image and local identifies applications and libraries that this operator
relies on to execute a task locally. For instance this is an operator for running
arbitrary Radiance commands.

```yaml
  - name: radiance-operator
    container:
      name: radiance52
      image: ladybugtools/radiance:5.2
    local:
      app:
        - name: radiance
          version: ">=5.2"
          command: rtrace -version  # command to get the version
          pattern: r'\d+\.\d+'  # regex pattern to extract the version from command output
```

Here is another one for running a `template` for running `honeybee-radiance` workflows.
This `operator` will run on Windows, Linux and Mac platforms. You can exclude a platform
by removing it from the list.

```yaml

  - name: honeybee-radiance
    container:
      name: honeybee-radiance
      image: ladybugtools/honeybee-radiance-workflow:latest
    local:
      app:
        - name: radiance
          version: ">=5.2"
          command: rtrace -version
          pattern: r'\d+\.\d+'
      pip:
        - name: lbt-honeybee
          version: ">=0.4.3"
        - name: honeybee-radiance-workflow
      language:
        - name: python
          version: ">=3.6"
      platform:
       - Windows
       - Linux
       - Mac

```

You can also import the operator from a `YAML` or `JSON` file using the `import_from`
key. All the fields except for the name will be loaded from the file. It's good practice
to use the same name inside the yaml file and the workflow.

```yaml

  - name: ladybug-operator
    import_from: /operators/ladybug_operator.yaml

```

## 3. templates

Templates are a discrete reusable unit of code that can be executed separately or as part
of a workflow. Queenbee supports 4 type of objects as templates:

- `module` : A single module. Each module uses an operator from operators section.
- `dag`: Collection of modules as a Directed Acyclic Graph (DAG).
- `steps`: Collection of modules to be executed sequentially in steps.
- `workflow`: A full Queenbee workflow itself can be referenced as a template in another
  workflow.

Templates can use the `import_from` keyword to import the `template` from a `YAML` or
`JSON` file. Keep in mind that a template in a file should be self-sufficient and include
all the information including `operator`s. This is different from when the `template` is
part of the `workflow` where an `operator` will be referenced by name.

Here is a `module` for generating a sky with desired irradiance which is part of a
workflow. In order to make it a valid `template` in a separate file you should use the
full operator specification from the last step instead of only using the name of the
operator.

```yaml
  name: generate_sky
  inputs:
    parameters:
      - name: desired_irradiance
        value: 100000   # default value which can be overwritten
  operator: radiance-operator
  # commands and args will be used both locally and inside the container
  command:
    - /bin/sh
    - -c
  args:
    - gensky -c -B '{{ inputs.parameters.desired_irradiance }}' > '{{ workflow.artifacts.sky }}'
  outputs:
    artifacts:
      - name: sky
        path: '{{ workflow.artifacts.sky }}'
```

Alternatively, you can use `honeybee-radiance` operator which has a command for
generating sky.

```yaml
  name: generate_sky
  inputs:
    parameters:
      - name: desired_irradiance
        value: 100000   # default value which can be overwritten
  operator: honeybee-radiance
  command:
    - honeybee-radiance
  args:
    - fixed-irradiance-sky
    - --irradiance
    - "{{inputs.parameters.desired_irradiance}}"
  outputs:
    artifacts:
      - name: sky
        path: '{{ workflow.artifacts.sky }}'
```

## 4. flow

`flow` is the heart of the workflow to define how the templates should be executed.
Queenbee supports two different types of workflows. DAGFlow and SteppedFlow. 

It's common to use the output of one step as an input for another step or reference one
of the workflow inputs as an input for one of the steps or tasks. Queenbee supports the
following words as prefix variable names::

- workflow: "{{workflow.xx.yy}} is used for workflow level parameters.
- steps: "{{steps.step_name.xx.yy}} is used in chained templates.
- tasks: "{{tasks.task_name.xx.yy}} is used in DAG task to refer to other tasks.
- inputs: "{{inputs.xx.yy}}" is used in operators.
- item: "{{item}}" or "{{item.key_name}}" is used in loops. You can change item to a
  different keyword by setting up `loop_var` in `loop_control`.

Here is a example of creating a sky and generating an octree as two consecutive steps.
Note that the values are place-holders and can be overwritten by input parameters file.

```yaml

flow:
  - steps:
    - name: generate_sky_step
      template: generate_sky
      inputs:
        parameters:
          - name: desired_irradiance
            value: 100000
    - name: generate_octree_step
      template: generate_octree
      inputs:
        parameters:
           - name: scene_files
             value:
               - "{{steps.generate_sky_steps.outputs.sky_file}}"
               - "{{workflow.inputs.parameters.folder}}"/model/static/scene.mat
               - "{{workflow.inputs.parameters.folder}}"/model/static/scene.rad

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
is the updated flow. Note the the keyword `step` is changed to `tasks` and each `task` has
a key for `dependency`.

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
             value:
               - "{{tasks.generate_sky_steps.outputs.sky_file}}"
               - "{{workflow.inputs.parameters.folder}}"/model/static/scene.mat
               - "{{workflow.inputs.parameters.folder}}"/model/static/scene.rad
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

## 5. outputs

Several files might be generated in the `flow` section and the `outputs` `artifcats`
section indicates which ones should be saved as the final outputs of the `workflow`.
Executors may return these outputs as a collection of file locations or file contents.

Outputs can also return `parameters` that are generated in the `flow` section of the
workflow. 


# Command Line Interface

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
{{steps.create_octree.outputs.artifacts.octree}}) will not be included in the inputs
file. 

## visualize

`queenbee visualize [WORKFLOW-FILE]`

This command creates an interactive visual representation of the workflow.

![image](https://user-images.githubusercontent.com/2915573/61600213-9405e280-abfd-11e9-91e7-a0a622ca3ece.png)
