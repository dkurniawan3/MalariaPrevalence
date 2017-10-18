'''Python implementation of malaria simulation'''

# pylint: disable=C0103
# pylint: disable=C0111
# pylint: disable=C1001
# pylint: disable=E0001
# pylint: disable=E1101

from __future__ import division
from collections import Counter
import random
import math
import numpy as np

class Person():

    def __init__(self, age):
        self.age = age
        self.relativeBitingRate = np.random.lognormal(1, 1.127)
        self.Immunity = self.getImmunity()
        self.infectionStatus = {1:'Uninfected'}

    def getImmunity(self):
        # This formula is subject to change based on CDC approvals
        self.Immunity = .88-(.8*math.exp(-.5*(-3.5+.1094*self.age)**2))
        return self.Immunity

    def UpdateInfectedStatus(self, status):
        self.infectionStatus = status

    def getExpectedNumBites(self, sumOfRBRs, totalNumMosquitoes, BitingRate):
        expectedNumBites = (self.relativeBitingRate/sumOfRBRs)*totalNumMosquitoes*BitingRate
        return expectedNumBites

    def getProbInfected(self, SusMosquitoes, totalNumMosquitoes, expectedBites):
        probInfectedInfectiousMosquito = (1 - (SusMosquitoes/totalNumMosquitoes)
                                          **(expectedBites)*self.Immunity)
        return probInfectedInfectiousMosquito

class Mosquito():

    def __init__(self, totalNumMosquitoes, SusceptibileMosquitoes, DeathRate):
        self.totalNumMosquitoes = totalNumMosquitoes
        self.SusceptibileMosquitoes = SusceptibileMosquitoes
        self.DeathRate = DeathRate

    def getInfectedMosquitoes(self):
        return self.totalNumMosquitoes - self.SusceptibileMosquitoes

    # def calcInfectedMosquitoes(self):
    #     self.infectedMosquitoes = self.getInfectedMosquitoes()*(1-self.DeathRate)

def main():

    # Parameters

    # Total # Mosquitoes is a value that we need to talk to the other CDC team about
    # If they have a way they can model this
    totalNumMosquitoes = 200
    # Bites per man per night
    BitingRate = 3
    # Recovery rate of humans (days)
    recovery_rate = 7
    # Arbitrary number of infected mosquitoes at time 0
    t0Infected = 50
    # Death Rate of Mosquitoes
    deathRate = 1/8

    # Generate 1000 persons: 30 of each age 0-14 and 11 of ages 15 to 64
    ageDist = sorted(range(0, 15)*30 + range(15, 65)*11)
    HumanDictionary = {}

    i = 0
    # Generate a Person instance for 1000 humans
    for personNum in ageDist:
        person = Person(personNum)
        HumanDictionary[i] = (personNum, person)
        i += 1

    # Calculate the sum of all human's relative biting rates
    sumOfRBRs = sum([value[1].relativeBitingRate for value in HumanDictionary.values()])

    # Instantiate Mosquito class
    Mosquitoes = Mosquito(totalNumMosquitoes, totalNumMosquitoes-t0Infected, deathRate)

    # Calculate Expcted Number of Bites, probability of getting infected when
    # bitten by infectious mosquito, infection status
    # All formulas derived from Protocol S1 (literature review)
    for k, v in HumanDictionary.items():
        expectedNumBites = v[1].getExpectedNumBites(sumOfRBRs, totalNumMosquitoes, BitingRate)
        probInfectedInfectiousMosquito = v[1].getProbInfected(Mosquitoes.SusceptibileMosquitoes,
                                                              Mosquitoes.totalNumMosquitoes,
                                                              expectedNumBites)

        # Probability getting infected at TIME 1 ONLY determined by random number generator 0-1
        randomNum = random.random()
        if randomNum < probInfectedInfectiousMosquito:
            v[1].UpdateInfectedStatus({1:'Infected'})
        HumanDictionary[k] = v + (probInfectedInfectiousMosquito,) + (expectedNumBites,) + (v[1].infectionStatus,)

    #Infectious states over time, taking into account recovery rate
    for k, v in HumanDictionary.items():
        for i in range(2, 20):
            j = i-1
            # If the current state is infected and the unit time is less than the recovery rate,
            # then human stays infected
            if v[4][j] == 'Infected':
                if i < recovery_rate:
                    v[4][i] = 'Infected'
                else:
                    # If unit time is greater than recovery rate:
                    # Check if the previous 7 stages were infected
                    # If yes the human goes into a state of protection (prophylaxis treatment)
                    # Otherwise, the human stays infected
                    if sum(1 if item == 'Infected' else 0 for item in v[4].values()[-7:]) == 7:
                        v[4][i] = 'Protected'
                    else:
                        v[4][i] = 'Infected'

            # If the current state is uninfected, determine probability they become infected and use
            # random number generator to determine infectiousness
            elif v[4][j] == 'Uninfected':
                expectedNumBites = v[1].getExpectedNumBites(sumOfRBRs, totalNumMosquitoes, BitingRate)
                probInfectedInfectiousMosquito = v[1].getProbInfected(Mosquitoes.SusceptibileMosquitoes,
                                                                      Mosquitoes.totalNumMosquitoes,
                                                                      expectedNumBites)
                randomNum = random.random()
                if randomNum < probInfectedInfectiousMosquito:
                    v[4][i] = 'Infected'
                else:
                    v[4][i] = 'Uninfected'

            # If the current state is protected, the human can stay in this state for 7 units time.
            # So, if the previous 7 states = protected, the human is then susceptible to infection
            # Calculate probability of infectiousness again and use RNG to determine infectiousness
            # If the human has not been in protected state for 7 units of time, stay in protected
            elif v[4][j] == 'Protected':
                if sum(1 if item == 'Protected' else 0 for item in v[4].values()[-7:]) == 7:
                    expectedNumBites = v[1].getExpectedNumBites(sumOfRBRs, totalNumMosquitoes, BitingRate)
                    probInfectedInfectiousMosquito = v[1].getProbInfected(Mosquitoes.SusceptibileMosquitoes,
                                                                          Mosquitoes.totalNumMosquitoes,
                                                                          expectedNumBites)
                    randomNum = random.random()
                    if randomNum < probInfectedInfectiousMosquito:
                        v[4][i] = 'Infected'
                    else:
                        v[4][i] = 'Uninfected'
                else:
                    v[4][i] = 'Protected'

    # Generating infected mosquitoes list over time
    # Instantiate time 0 and time 1 conditions
    InfectedMosquitoesList = []
    InfectedMosquitoesList.append(t0Infected)

    # At time 1, the number of infected mosquitoes is just previous number of infected
    # multiplied by (1- death rate)
    current_Infected = math.ceil(t0Infected*(1-Mosquitoes.DeathRate))
    InfectedMosquitoesList.append(current_Infected)

    # Count number of uninfected (otherwise known as susceptible) humans
    statuses = [HumanDictionary[k][4] for k in HumanDictionary]
    susHumans = Counter(stat[1] for stat in statuses)

    # Calculate number of infected mosquitoes at time 2 and onwards
    # Equations found from Protocol S1
    for i in range(2, 10):
        new_Infected = (1-Mosquitoes.DeathRate)*(current_Infected+(1-(susHumans['Uninfected']
                                                                      /len(statuses))**BitingRate)*
                                                 (Mosquitoes.totalNumMosquitoes-current_Infected))
        InfectedMosquitoesList.append(math.ceil(new_Infected))
        current_Infected = new_Infected

    # Print out just one instance of a person in the dictionary, and the list of # infectious
    # Mosquitos over time
    print 'Age:', HumanDictionary[100][0]
    print 'Probability Getting Infected by Infectious Mosquito:', HumanDictionary[100][2]
    print 'Expected Number of Bites:', HumanDictionary[100][3]
    print 'Infection Status:', HumanDictionary[100][4]
    print 'Infected Mosquitoes per Unit Time 1-10:', InfectedMosquitoesList
    print '--------------------------------------'

    # Print out the entire dictionary of 1000 persons
    # print HumanDictionary

if __name__ == '__main__':
    main()
