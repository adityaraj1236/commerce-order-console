import "./global_components.css";

interface ProductIdentityProps {
  name: string;
  sku: string;
}

/** Product name with its SKU underneath: the same everywhere a product is listed. */
export function ProductIdentity({ name, sku }: ProductIdentityProps) {
  return (
    <div className="product-identity">
      <span className="product-identity-name">{name}</span>
      <span className="product-identity-sku">{sku}</span>
    </div>
  );
}
