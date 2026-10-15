# Untitled object in list-findings output Schema

```txt
http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items
```



| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                               |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Allowed               | none                | [list-findings-output.json\*](insights/list-findings-output.json "open original schema") |

## items Type

`object` ([Details](list-findings-output-properties-findings-items.md))

# items Properties

| Property                              | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                                     |
| :------------------------------------ | :-------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [id](#id)                             | `string`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-id.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/id")                             |
| [severity](#severity)                 | `string`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-severity.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/severity")                 |
| [title](#title)                       | `string`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-title.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/title")                       |
| [summary](#summary)                   | `string`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-summary.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/summary")                   |
| [suggested_action](#suggested_action) | `string`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-suggested_action.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/suggested_action") |
| [modules](#modules)                   | `array`   | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-modules.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/modules")                   |
| [evidence](#evidence)                 | `array`   | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-evidence.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/evidence")                 |
| [status](#status)                     | `string`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-status.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/status")                     |
| [occurrence_count](#occurrence_count) | `integer` | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-occurrence_count.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/occurrence_count") |
| [first_seen](#first_seen)             | `integer` | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-first_seen.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/first_seen")             |
| [last_seen](#last_seen)               | `integer` | Required | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-last_seen.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/last_seen")               |
| [reopened_at](#reopened_at)           | `integer` | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-reopened_at.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/reopened_at")           |
| [nodes](#nodes)                       | `array`   | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-nodes.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/nodes")                       |
| [node_refs](#node_refs)               | `array`   | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-node_refs.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs")               |
| [doc_ref](#doc_ref)                   | `string`  | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-doc_ref.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/doc_ref")                   |
| [security](#security)                 | `boolean` | Optional | cannot be null | [list-findings output](list-findings-output-properties-findings-items-properties-security.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/security")                 |

## id



`id`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-id.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/id")

### id Type

`string`

## severity



`severity`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-severity.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/severity")

### severity Type

`string`

### severity Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value        | Explanation |
| :----------- | :---------- |
| `"critical"` |             |
| `"high"`     |             |
| `"medium"`   |             |
| `"low"`      |             |

## title



`title`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-title.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/title")

### title Type

`string`

## summary



`summary`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-summary.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/summary")

### summary Type

`string`

## suggested_action



`suggested_action`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-suggested_action.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/suggested_action")

### suggested_action Type

`string`

## modules



`modules`

* is required

* Type: `string[]`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-modules.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/modules")

### modules Type

`string[]`

## evidence



`evidence`

* is optional

* Type: `string[]`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-evidence.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/evidence")

### evidence Type

`string[]`

## status



`status`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-status.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/status")

### status Type

`string`

### status Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value     | Explanation |
| :-------- | :---------- |
| `"open"`  |             |
| `"stale"` |             |

## occurrence_count



`occurrence_count`

* is optional

* Type: `integer`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-occurrence_count.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/occurrence_count")

### occurrence_count Type

`integer`

## first_seen

Unix time in milliseconds

`first_seen`

* is optional

* Type: `integer`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-first_seen.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/first_seen")

### first_seen Type

`integer`

## last_seen

Unix time in milliseconds

`last_seen`

* is required

* Type: `integer`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-last_seen.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/last_seen")

### last_seen Type

`integer`

## reopened_at

Unix time in milliseconds

`reopened_at`

* is optional

* Type: `integer`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-reopened_at.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/reopened_at")

### reopened_at Type

`integer`

## nodes



`nodes`

* is optional

* Type: `integer[]`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-nodes.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/nodes")

### nodes Type

`integer[]`

## node_refs



`node_refs`

* is optional

* Type: `object[]` ([Details](list-findings-output-properties-findings-items-properties-node_refs-items.md))

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-node_refs.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/node_refs")

### node_refs Type

`object[]` ([Details](list-findings-output-properties-findings-items-properties-node_refs-items.md))

## doc_ref



`doc_ref`

* is optional

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-doc_ref.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/doc_ref")

### doc_ref Type

`string`

## security



`security`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings-items-properties-security.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/security")

### security Type

`boolean`
