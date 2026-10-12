# Untitled object in list-findings output Schema

```txt
http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs/items
```



| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                               |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Allowed               | none                | [list-findings-output.json\*](insights/list-findings-output.json "open original schema") |

## items Type

`object` ([Details](list-findings-output-properties-findings-items-properties-node_refs-items.md))

# items Properties

| Property            | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                                                                         |
| :------------------ | :-------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [node_id](#node_id) | `integer` | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-node_refs-items-properties-node_id.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs/items/properties/node_id") |
| [fqdn](#fqdn)       | `string`  | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-node_refs-items-properties-fqdn.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs/items/properties/fqdn")       |

## node_id



`node_id`

* is optional

* Type: `integer`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-node_refs-items-properties-node_id.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs/items/properties/node_id")

### node_id Type

`integer`

## fqdn



`fqdn`

* is optional

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-node_refs-items-properties-fqdn.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs/items/properties/fqdn")

### fqdn Type

`string`
