# Deepwick

Obsidian with the **Deepwick** palette, derived from *Polywick Blue*.

## Links and code

See [[Palette]] and [[Missing note]], or read [the spec](https://github.com/deepwick/spec). Inline `code` is Orange.

```python
from dataclasses import dataclass


@dataclass
class Swatch:
    name: str
    ratio: float


def passes(swatch, minimum=4.5):
    # Text must reach 4.5:1 on Background.
    if swatch.ratio >= minimum:
        return swatch.name + " passes"
    return None


print(passes(Swatch("Blue", 6.87)))
```

    indented code stays plain

### Callouts and lists

> [!info] Info
> Blue, like headings.

> [!warning] Warning
> Yellow.

> [!example] Example
> Magenta.

- [x] Port the palette #deepwick
- [ ] Publish the theme

> Quotes are Comment italic.

==Highlights== use the Selection color.

| Role | Color |
|---|---|
| Keyword | Blue |
| String | Orange |
