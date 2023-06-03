import React, { useState, useEffect } from 'react';
import { Button, Table, message, Layout, ConfigProvider, theme, Menu } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, BulbOutlined } from '@ant-design/icons';
import './FileUpload.css';


import MatterAntimatterIcon from './img/Generic_Warp_Core.webp';
import SingularityIcon from './img/Generic_Singularity_Core.webp';
import LockBoxIcon from './img/lock_box.webp';
import ZenIcon from './img/Zen_small_icon.webp';
import LobiIcon from './img/Lobi_Crystal_icon.webp';
import LifetimeIcon from './img/Stalwart_icon.webp';
import ECIcon from './img/Energy_credit_icon.webp';
import FleetCreditsIcon from './img/Fleet_Credit_icon.webp';
import FleetModuleIcon from './img/Fleet_Ship_Module_icon.webp';
import PromoIcon from './img/Special_Requisition_Choice_Pack_-_Tier_6_Promotional_Ship_Choice_Pack_icon.webp';
import PhoenixIcon from './img/Epic_icon.webp';
import DilithiumIcon from './img/Refined_dilithium_icon.webp';
import ConsoleTacIcon from './img/Console_tac_icon.webp';
import ConsoleEngIcon from './img/Console_eng_icon.webp';
import ConsoleSciIcon from './img/Console_sci_icon.webp';
import ConsoleUniIcon from './img/Console_uni_icon.webp';
import SRFED2Icon from './img/SRFED2.webp';
import SRFED3Icon from './img/SRFED3.webp';
import SRFED4Icon from './img/SRFED4.webp';
import SRFED5Icon from './img/SRFED5.webp';
import SRKDF2Icon from './img/SRKDF2.webp';
import SRKDF3Icon from './img/SRKDF3.webp';
import SRKDF4Icon from './img/SRKDF4.webp';
import SRKDF5Icon from './img/SRKDF5.webp';
import AppProgressIcon from './img/Appointment_Progress_icon.webp';
import UpgradeTokenIcon from './img/Upgrade.webp';



const App = () => {
    const [tableData, setTableData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleButtonClick = async () => {
        setIsLoading(true);
        message.loading('Skripte werden ausgeführt...', 0);

        try {
            const response = await fetch('http://localhost:5000/run-scripts');
            const data = await response.json();

            setIsLoading(false);

            if (data.error) {
                message.error('Fehler beim Ausführen der Skripte: ' + data.error);
            } else {
                await downloadResult();
            }
        } catch (error) {
            setIsLoading(false);
            message.error('Fehler beim Ausführen der Skripte: ' + error);
        }
    };

    const downloadResult = async () => {
        try {
            const response = await fetch('http://localhost:5000/download-result');
            const data = await response.json();
            setTableData(data);
            message.success('Skripte wurden erfolgreich ausgeführt.', 2); // Die Nachricht für 2 Sekunden anzeigen
        } catch (error) {
            console.error('Fehler beim Herunterladen des Ergebnisses:', error);
        }
    };

    useEffect(() => {
        if (!isLoading) {
            message.destroy();
        }
        const fetchTableData = async () => {
            try {
                const response = await fetch('http://localhost:5000/download-result');
                const data = await response.json();
                setTableData(data);
            } catch (error) {
                console.error('Fehler beim Laden der Daten:', error);
            }
        };

        fetchTableData();
    }, [isLoading]);



    const numericSorter = (a, b, key) => {
        const valueA = Number(a[key]);
        const valueB = Number(b[key]);

        if (!isNaN(valueA) && !isNaN(valueB)) {
            return valueA - valueB;
        }

        const stringA = String(a[key]);
        const stringB = String(b[key]);
        return stringA.localeCompare(stringB);
    };

    const generateColumns = () => {
        if (tableData.length === 0) {
            return [];
        }

        const keyOrder = [
            'Ship',
            'Tier',
            'Type',
            'Fore Weapons',
            'Aft Weapons',
            'Dual Cannons',
            'Max Hull',
            'Hull modifier',
            'Shield modifier',
            'Turn rate',
            'Impulse modifier',
            'Inertia rating',
            'Device slots',
            'Consoles',
            'Hangar Bays',
            'Type-specific slot',
            'Upgrade cost',
            'Cost',
            'Released',
            'Link',
        ];

        const excludedColumns = ['Warp core', 'Bonus Power', 'Abilities', 'Admiralty stats', 'Link'];

        const filteredKeys = keyOrder.filter((key) => !excludedColumns.includes(key));

        return filteredKeys.map((key) => {
            const column = {
                title: key,
                dataIndex: key,
                key: key,
                sorter: (a, b) => numericSorter(a, b, key),
                sortDirections: ['ascend', 'descend'],
                width: undefined,
            };

            if (key === 'Dual Cannons') {
                column.render = (text) => {
                    if (text === 'yes') {
                        return <CheckCircleOutlined style={{ color: 'green' }} />;
                    } else if (text === 'no') {
                        return <CloseCircleOutlined style={{ color: 'red' }} />;
                    } else {
                        return null;
                    }
                };
            } else if (key === 'Warp core') {
                column.render = (text) => {
                    if (text === 'Matter-Antimatter') {
                        return <img src={MatterAntimatterIcon} alt="Matter-Antimatter" />;
                    } else if (text === 'Singularity') {
                        return <img src={SingularityIcon} alt="Singularity" />;
                    } else {
                        return text;
                    }
                };

            } else if (key === 'Consoles') {
                column.width = 120;
                column.render = (text) => {
                    if (text) {
                        const replacedText = text
                            .replace('Console eng icon', `<img src=${ConsoleEngIcon} alt="Console eng icon" />`)
                            .replace('Console tac icon', `<img src=${ConsoleTacIcon} alt="Console tac icon" />`)
                            .replace('Console sci icon', `<img src=${ConsoleSciIcon} alt="Console sci icon" />`)
                            .replace('Console uni icon', `<img src=${ConsoleUniIcon} alt="Console uni icon" />`);

                        return <div dangerouslySetInnerHTML={{ __html: replacedText }} />;
                    }
                };

            } else if (key === 'Upgrade cost') {
                column.render = (text) => {
                    if (text) {
                        const replacedText = text
                            .replace('Upgrade', `<img src=${UpgradeTokenIcon} alt="Upgrade Token" />`);
                        return <div dangerouslySetInnerHTML={{ __html: replacedText }} />;
                    }
                };

            } else if (key === 'Ship') {
                column.render = (text, record) => {
                    const link = record.Link;
                    if (link) {
                        return (
                            <a href={link} target="_blank" rel="noopener noreferrer">
                                {text}
                            </a>
                        );
                    }
                    return text;
                };

                // Text als Tag anzeigen
                //            } else if (key === 'Type-specific slot') {
                //                column.render = (text) => {
                //                    if (text === 'Experimental Weapon') {
                //                        return <Tag>{text}</Tag>;
                //                    } else {
                //                        return text;
                //                    }
                //                };

            } else if (key === 'Cost') {
                column.render = (text) => {
                    if (text) {
                        const replacedText = text
                            .replace('Generic Lock Box v2', `<img src=${LockBoxIcon} alt="Generic Lock Box v2" />`)
                            .replace('Lobi Crystal icon', `<img src=${LobiIcon} alt="Lobi Crystal icon" />`)
                            .replace('Zen small icon', `<img src=${ZenIcon} alt="Zen small icon" />`)
                            .replace('Stalwart icon', `<img src=${LifetimeIcon} alt="Stalwart icon" />`)
                            .replace('Energy credit icon', `<img src=${ECIcon} alt="Energy credit icon" />`)
                            .replace('Fleet Credits', `<img src=${FleetCreditsIcon} alt="Fleet Credits" />`)
                            .replace('Fleet Ship Module icon', `<img src=${FleetModuleIcon} alt="Fleet Ship Module icon" />`)
                            .replace('Special Requisition Choice Pack - Tier 6 Promotional Ship Choice Pack icon', `<img src=${PromoIcon} alt="Special Requisition Choice Pack - Tier 6 Promotional Ship Choice Pack icon" />`)
                            .replace('Epic Prize Token - Phoenix Prize Pack icon Epic icon', `<img src=${PhoenixIcon} alt="Phoenix Prize Pack Epic Icon" />`)
                            .replace('SRFED2', `<img src=${SRFED2Icon} alt="Starship Requisition (Lt. Cmdr.)" />`)
                            .replace('SRFED3', `<img src=${SRFED3Icon} alt="Starship Requisition (Cmdr.)" />`)
                            .replace('SRFED4', `<img src=${SRFED4Icon} alt="Starship Requisition (Capt.)" />`)
                            .replace('SRFED5', `<img src=${SRFED5Icon} alt="Starship Requisition (Adm.)" />`)
                            .replace('SRKDF2', `<img src=${SRKDF2Icon} alt="Starship Requisition (Lt. Cmdr.)" />`)
                            .replace('SRKDF3', `<img src=${SRKDF3Icon} alt="Starship Requisition (Cmdr.)" />`)
                            .replace('SRKDF4', `<img src=${SRKDF4Icon} alt="Starship Requisition (Capt.)" />`)
                            .replace('SRKDF5', `<img src=${SRKDF5Icon} alt="Starship Requisition (Adm.)" />`)
                            .replace('Appointment Progress', `<img src=${AppProgressIcon} alt="Appointment Progress" />`)
                            .replace('Refined dilithium icon', `<img src=${DilithiumIcon} alt="Refined dilithium icon" />`);

                        return <div dangerouslySetInnerHTML={{ __html: replacedText }} />;
                    }
                };
            } else {
                // Setze CloseCircleOutlined bei leerer Zelle
                column.render = (text) => {
                    if (!text) {
                        return <CloseCircleOutlined style={{ color: 'red' }} />;
                    }
                    return text;
                };
            }



            return column;
        });
    };

    const columns = generateColumns();

    const { Header, Content } = Layout;
    const { defaultAlgorithm, darkAlgorithm } = theme;
    const [isDarkMode, setIsDarkMode] = useState(false);
    const handleClick = () => {
        setIsDarkMode((previousValue) => !previousValue);
    };

    return (
        <ConfigProvider theme={{ algorithm: isDarkMode ? darkAlgorithm : defaultAlgorithm }}>
            <Layout style={{ minHeight: '100vh' }}>
                <Header >

                    <Menu mode="horizontal" style={{ display: 'flex', justifyContent: 'center' }}>
                        <Menu.Item key="1" icon={<BulbOutlined />} onClick={handleClick} style={{ width: 'max-content' }}>
                            Change Theme to {isDarkMode ? 'Light' : 'Dark'}
                        </Menu.Item>
                        <Menu.Item key="2">
                            <Button onClick={handleButtonClick} loading={isLoading}>Daten neu scrapen</Button>
                        </Menu.Item>
                    </Menu>
                </Header>
                <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <div style={{ width: '85%' }}>
                        <Table
                            dataSource={tableData}
                            columns={columns}
                            pagination={false}
                            size="small"
                            scroll={{ x: true }}
                            className="small-text"
                        />
                    </div>
                </Content>
            </Layout>
        </ConfigProvider>
    );
};

export default App;
