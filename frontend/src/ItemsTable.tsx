import { useEffect, useState } from "react";

interface Item {
    id: number;
    name: string;
    type: string;
    price: number;
}

export default function ItemsTable(): JSX.Element {
    const [items, setItems] = useState<Item[]>([]);

    useEffect(() => {
        async function load(): Promise<void> {
            const res = await fetch("/items");
            const data: Item[] = await res.json();
            setItems(data);
        }

        load();
    }, []);

    return (
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Price</th>
                </tr>
            </thead>

            <tbody>
                {items.map((item) => (
                    <tr key={item.id}>
                        <td>{item.id}</td>
                        <td>{item.name}</td>
                        <td>{item.type}</td>
                        <td>{item.price}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}