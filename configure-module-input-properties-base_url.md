# Untitled string in configure-module input Schema

```txt
http://schema.nethserver.org/insights/configure-module-input.json#/properties/base_url
```

Root URL of the insights server, with no path. If omitted, the current value is kept (initially <https://insights.nethesis.it>)

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                   |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [configure-module-input.json\*](insights/configure-module-input.json "open original schema") |

## base_url Type

`string`

## base_url Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^https?://
```

[try pattern](https://regexr.com/?expression=%5Ehttps%3F%3A%2F%2F "try regular expression with regexr.com")

**URI**: the string must be a URI, according to [RFC 3986](https://tools.ietf.org/html/rfc3986 "check the specification")
