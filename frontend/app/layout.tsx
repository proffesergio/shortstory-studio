import type {Metadata} from 'next';
import './globals.css';
export const metadata: Metadata = {title:'StoryShorts Studio',description:'Local-first AI story video production'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
