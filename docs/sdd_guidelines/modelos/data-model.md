# Modelo de dados

**Funcionalidade:** [nome]  
**Spec:** [link]

Descreva entidades e regras do domínio. Tipos específicos de banco pertencem ao plano ou à implementação.

## Entidade [nome]

**Finalidade:** [o que representa]

| Campo | Significado | Obrigatório | Regras |
|---|---|---:|---|
| `id` | Identificador estável | sim | único e não vazio |
| [campo] | [significado] | [sim ou não] | [validação] |

## Relacionamentos

- [Entidade A] possui [relação] com [Entidade B].

## Estados e transições

```text
[estado inicial] -> [estado intermediário] -> [estado final]
```

- A transição ocorre quando [condição].
- A transição é rejeitada quando [condição].

## Validações transversais

- [regra entre campos ou entidades]
- [regra de retenção, integridade ou privacidade]
