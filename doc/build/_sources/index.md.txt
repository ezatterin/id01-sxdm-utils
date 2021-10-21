<!-- .. id01-sxdm-utils documentation master file, created by
   sphinx-quickstart on Thu Oct 21 15:58:38 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive. -->

# Welcome to id01-sxdm-utils's documentation!

Contents:

<!-- Need to use a directive that evals rst code due to autodoc -->
```{eval-rst}
.. toctree::
   :maxdepth: 2

   io.md
```

<!-- Here instead the directive does something itself -->
```{admonition} Wow!
   :class: danger
   This is an `{admonition}` directive!
```

```{danger} 
   Dangerousssssss
```

(subsec)= 
## This is a subsection

Hello!

And here is a {ref}`reference to it <subsec>`.
And [another one](subsec).
And one to [io](io).

Some python code:
```python
print('Hello!')
```

