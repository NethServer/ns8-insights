# configure-module input Schema

```txt
http://schema.nethserver.org/insights/configure-module-input.json
```

Enable or disable the insights collector

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                 |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :----------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [configure-module-input.json](insights/configure-module-input.json "open original schema") |

## configure-module input Type

`object` ([configure-module input](configure-module-input.md))

## configure-module input Examples

```json
{
  "enabled": true,
  "base_url": "https://insights.nethesis.it",
  "verify_tls": true
}
```

```json
{
  "enabled": false
}
```

# configure-module input Properties

| Property                  | Type      | Required | Nullable       | Defined by                                                                                                                                                           |
| :------------------------ | :-------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [enabled](#enabled)       | `boolean` | Required | cannot be null | [configure-module input](configure-module-input-properties-enabled.md "http://schema.nethserver.org/insights/configure-module-input.json#/properties/enabled")       |
| [base_url](#base_url)     | `string`  | Optional | cannot be null | [configure-module input](configure-module-input-properties-base_url.md "http://schema.nethserver.org/insights/configure-module-input.json#/properties/base_url")     |
| [verify_tls](#verify_tls) | `boolean` | Optional | cannot be null | [configure-module input](configure-module-input-properties-verify_tls.md "http://schema.nethserver.org/insights/configure-module-input.json#/properties/verify_tls") |

## enabled

Run the collector. Requires a cluster subscription and no other enabled insights instance in the cluster.

`enabled`

* is required

* Type: `boolean`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-enabled.md "http://schema.nethserver.org/insights/configure-module-input.json#/properties/enabled")

### enabled Type

`boolean`

## base_url

Root URL of the insights server, with no path. If omitted, the current value is kept (initially <https://insights.nethesis.it>)

`base_url`

* is optional

* Type: `string`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-base_url.md "http://schema.nethserver.org/insights/configure-module-input.json#/properties/base_url")

### base_url Type

`string`

### base_url Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^https?://
```

[try pattern](https://regexr.com/?expression=%5Ehttps%3F%3A%2F%2F "try regular expression with regexr.com")

**URI**: the string must be a URI, according to [RFC 3986](https://tools.ietf.org/html/rfc3986 "check the specification")

## verify_tls

Verify the TLS certificate of the insights server. If omitted, the current value is kept (initially true)

`verify_tls`

* is optional

* Type: `boolean`

* cannot be null

* defined in: [configure-module input](configure-module-input-properties-verify_tls.md "http://schema.nethserver.org/insights/configure-module-input.json#/properties/verify_tls")

### verify_tls Type

`boolean`
