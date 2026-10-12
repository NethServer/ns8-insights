# Untitled string in list-findings output Schema

```txt
http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/severity
```



| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                               |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [list-findings-output.json\*](insights/list-findings-output.json "open original schema") |

## severity Type

`string`

## severity Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value        | Explanation |
| :----------- | :---------- |
| `"critical"` |             |
| `"high"`     |             |
| `"medium"`   |             |
| `"low"`      |             |
