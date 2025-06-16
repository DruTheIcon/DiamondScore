# DiamondScore
A Baseball themed app

import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, StyleSheet, Image, SafeAreaView, ScrollView, Button, Alert, FlatList, TouchableOpacity,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ProgressBar } from 'react-native-paper';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

const Tab = createBottomTabNavigator();

const RANKS = [
  { level: 1, title: 'Tee-Ball' },
  { level: 8, title: 'Little League' },
  { level: 15, title: 'Varsity' },
  { level: 25, title: 'College' },
  { level: 40, title: 'Minor Leagues' },
  { level: 50, title: 'Major Leagues' },
  { level: 70, title: 'MVP' },
  { level: 100, title: 'Hall of Fame' },
];

const getRank = (level) => {
  let rank = 'Unranked';
  for (let i = RANKS.length - 1; i >= 0; i--) {
    if (level >= RANKS[i].level) {
      rank = RANKS[i].title;
      break;
    }
  }
  return rank;
};

const getXPForLevel = (level) => {
  return 100 + (level - 1) * ((10000 - 100) / 99);
};

function HomeFeedScreen({ level }) {
  const [feed, setFeed] = useState([
    { id: '1', username: 'AceHitter32', stats: '3 for 4, 2 HR, 5 RBI', level: 28 },
    { id: '2', username: 'PitchKing9', stats: '6 IP, 10 K, 0 ER', level: 50 },
    { id: '3', username: 'GloveWizard', stats: '3 amazing plays at SS!', level: 12 },
  ]);

  const handleLike = (id) => Alert.alert('You liked an outing!');
  const handleComment = (id) => Alert.alert('Comment feature coming soon!');

  const renderItem = ({ item }) => (
    <View style={styles.feedCard}>
      <Text style={styles.feedUsername}>{item.username} (Lv. {item.level})</Text>
      <Text style={styles.feedStats}>{item.stats}</Text>
      <View style={styles.feedActions}>
        <TouchableOpacity onPress={() => handleLike(item.id)}>
          <Ionicons name="heart-outline" size={24} color="#1e3a8a" />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => handleComment(item.id)} style={{ marginLeft: 16 }}>
          <Ionicons name="chatbubble-outline" size={24} color="#1e3a8a" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <FlatList
      data={feed}
      renderItem={renderItem}
      keyExtractor={(item) => item.id}
      contentContainerStyle={{ padding: 20 }}
    />
  );
}

function NewOutingScreen({ updateXP }) {
  const [outing, setOuting] = useState({
    Hits: '', ABs: '', PA: '', HRs: '', '1B': '', '2B': '', '3B': '', SB: '', K: '', BB: '',
    IP: '', BF: '', '#P': '', TB: '', TS: '', HA: '', RA: '', SO: '', HBP: '', ERA: '', WHIP: '', WP: ''
  });

  const handleChange = (key, value) => {
    setOuting(prev => ({ ...prev, [key]: value }));
  };

  const saveOuting = async () => {
    try {
      const battingKeys = ['Hits', 'ABs', 'PA', 'HRs', '1B', '2B', '3B', 'SB', 'K', 'BB'];
      const pitchingKeys = ['IP', 'BF', '#P', 'TB', 'TS', 'HA', 'RA', 'BB', 'SO', 'HBP', 'ERA', 'WHIP', 'WP'];
      const battingStats = JSON.parse(await AsyncStorage.getItem('battingStats')) || {};
      const pitchingStats = JSON.parse(await AsyncStorage.getItem('pitchingStats')) || {};

      let earnedXP = 0;
      const hits = parseInt(outing.Hits || 0);
      if (hits > 1) earnedXP += (hits - 1) * 50;

      const IP = parseFloat(outing.IP || 0);
      const walks = parseInt(outing.BB || 0);
      const SO = parseInt(outing.SO || 0);
      const HA = parseInt(outing.HA || 0);
      const RA = parseInt(outing.RA || 0);

      if (HA === 0 && IP >= 7) earnedXP += 100;
      if (HA === 0 && RA === 0 && walks === 0 && SO >= 21) earnedXP += 350;
      if (walks === 0 && IP >= 3) earnedXP += 50;
      if (SO >= 10) earnedXP += 75;

      earnedXP += 25; // streak bonus

      battingKeys.forEach(key => {
        battingStats[key] = ((parseFloat(battingStats[key] || 0)) + parseFloat(outing[key] || 0)).toString();
      });

      pitchingKeys.forEach(key => {
        pitchingStats[key] = ((parseFloat(pitchingStats[key] || 0)) + parseFloat(outing[key] || 0)).toString();
      });

      await AsyncStorage.setItem('battingStats', JSON.stringify(battingStats));
      await AsyncStorage.setItem('pitchingStats', JSON.stringify(pitchingStats));
      updateXP(earnedXP);
      Alert.alert('Outing Saved!');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <ScrollView style={styles.statsContainer}>
      <Text style={styles.title}>New Outing</Text>
      {Object.entries(outing).map(([key, value]) => (
        <TextInput
          key={key}
          style={styles.input}
          placeholder={key}
          value={value.toString()}
          onChangeText={text => handleChange(key, text)}
          keyboardType="numeric"
        />
      ))}
      <Button title="Save Outing" onPress={saveOuting} />
    </ScrollView>
  );
}

function StatsScreen() {
  const [battingStats, setBattingStats] = useState({});
  const [pitchingStats, setPitchingStats] = useState({});

  useEffect(() => {
    const fetchStats = async () => {
      const batting = JSON.parse(await AsyncStorage.getItem('battingStats')) || {};
      const pitching = JSON.parse(await AsyncStorage.getItem('pitchingStats')) || {};
      setBattingStats(batting);
      setPitchingStats(pitching);
    };
    fetchStats();
  }, []);

  return (
    <SafeAreaView style={styles.statsContainer}>
      <ScrollView>
        <Text style={styles.title}>📊 Player Stats</Text>
        <View style={styles.halfBox}>
          <Text style={styles.sectionTitle}>Batting Stats</Text>
          {Object.entries(battingStats).map(([key, value]) => (
            <Text key={key}>{key}: {value}</Text>
          ))}
        </View>
        <View style={styles.halfBox}>
          <Text style={styles.sectionTitle}>Pitching Stats</Text>
          {Object.entries(pitchingStats).map(([key, value]) => (
            <Text key={key}>{key}: {value}</Text>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function RankScreen({ level }) {
  return (
    <SafeAreaView style={styles.centered}>
      <Text style={styles.title}>🏆 Your Rank</Text>
      <Text style={{ fontSize: 24, fontWeight: 'bold' }}>{getRank(level)}</Text>
    </SafeAreaView>
  );
}

export default function App() {
  const [username, setUsername] = useState('PlayerOne');
  const [level, setLevel] = useState(1);
  const [xp, setXp] = useState(0);
  const [xpProgress, setXpProgress] = useState(0);

  useEffect(() => {
    const loadXP = async () => {
      const savedXP = parseInt(await AsyncStorage.getItem('xp') || '0');
      const savedLevel = parseInt(await AsyncStorage.getItem('level') || '1');
      setXp(savedXP);
      setLevel(savedLevel);
      const nextLevelXP = getXPForLevel(savedLevel);
      setXpProgress(savedXP / nextLevelXP);
    };
    loadXP();
  }, []);

  const updateXP = async (earned) => {
    let newXP = xp + earned;
    let newLevel = level;
    let nextLevelXP = getXPForLevel(newLevel);

    while (newXP >= nextLevelXP) {
      newXP -= nextLevelXP;
      newLevel++;
      nextLevelXP = getXPForLevel(newLevel);
    }

    setXp(newXP);
    setLevel(newLevel);
    setXpProgress(newXP / nextLevelXP);
    await AsyncStorage.setItem('xp', newXP.toString());
    await AsyncStorage.setItem('level', newLevel.toString());
  };

  const renderHeader = () => (
    <View style={styles.topProfile}>
      <Image source={{ uri: 'https://i.pravatar.cc/100?img=15' }} style={styles.profileImage} />
      <View style={styles.profileDetails}>
        <Text style={styles.level}>Lv. {level} - {getRank(level)}</Text>
        <TextInput style={styles.username} value={username} onChangeText={setUsername} />
        <ProgressBar progress={xpProgress} color="#10b981" style={styles.progressBar} />
      </View>
      <Text style={styles.streak}>🔥</Text>
    </View>
  );

  return (
    <SafeAreaView style={{ flex: 1 }}>
      {renderHeader()}
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ color, size }) => {
              let iconName;
              if (route.name === 'Stats') iconName = 'stats-chart';
              else if (route.name === 'New Outing') iconName = 'add-circle';
              else if (route.name === 'Rank') iconName = 'trophy';
              else if (route.name === 'Feed') iconName = 'home';
              return <Ionicons name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: '#1e3a8a',
            tabBarInactiveTintColor: 'gray',
            headerShown: false,
          })}
        >
          <Tab.Screen name="Feed">{() => <HomeFeedScreen level={level} />}</Tab.Screen>
          <Tab.Screen name="Stats" component={StatsScreen} />
          <Tab.Screen name="New Outing">{() => <NewOutingScreen updateXP={updateXP} />}</Tab.Screen>
          <Tab.Screen name="Rank">{() => <RankScreen level={level} />}</Tab.Screen>
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 10 },
  statsContainer: { flex: 1, padding: 20 },
  halfBox: { marginBottom: 20 },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 8 },
  input: {
    backgroundColor: '#fff', padding: 10, marginBottom: 10,
    borderRadius: 8, borderColor: '#ddd', borderWidth: 1
  },
  topProfile: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#1e3a8a', padding: 20
  },
  profileImage: {
    width: 64, height: 64, borderRadius: 32, borderWidth: 2, borderColor: '#fff'
  },
  profileDetails: { marginLeft: 16, flex: 1 },
  level: { color: '#fff', fontSize: 16, marginBottom: 2 },
  username: {
    color: '#fff', fontSize: 20, fontWeight: 'bold', borderBottomWidth: 1, borderBottomColor: '#fff'
  },
  progressBar: { height: 8, borderRadius: 4, backgroundColor: '#fff', marginTop: 6 },
  streak: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  feedCard: {
    backgroundColor: '#f0f4f8', padding: 16, borderRadius: 12, marginBottom: 16,
    borderColor: '#cbd5e1', borderWidth: 1
  },
  feedUsername: { fontWeight: 'bold', fontSize: 16, marginBottom: 4 },
  feedStats: { fontSize: 14, marginBottom: 8 },
  feedActions: { flexDirection: 'row' },
});
