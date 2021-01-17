import nltk 
import re
from nltk.stem import WordNetLemmatizer  
from nltk.corpus import stopwords
import numpy as np
import csv
import win32file
import win32pipe

def createBagOfWords(sentence): #Input cümlesinden anahtar kelimeleri alan fonksiyon
    
    tokenizer = nltk.RegexpTokenizer(r"\w+") #TOKENIZE INTO LIST
    new_words = tokenizer.tokenize(sentence)
    new_words = [index for index in new_words if not index in stop_words] #REMOVE FROM STOP WORDS
    new_words = [index.lower() for index in new_words] #MAKE LOWERCASE ALL OF THE WORDS
    new_words = [re.sub(r'\d+', '', index) for index in new_words] #REMOVE FROM NUMBERS
    new_words = [lemmatizer.lemmatize(index) for index in new_words] #REMOVE FROM GRAMMAR OF WORDS
    return new_words

def termFrequency(data,document): #input key dizisindeki her bir wordün kendi içinde kaç kez tekrarladığını hesaplayıp word : frekans şeklinde bir dictionary'e atar
    
    frequencies = {}
    counter = 0
    
    for word in data:
        for index in document:
            if(word == index):
                counter+=1
            
        frequencies.update({word:counter/len(data)})
        counter = 0
        
    return frequencies


def InverseDocumentFrequency(data,dictionaryDataset): #input anahtar kelimelerinin, dataset key cümlelerinin içinde bulunma sıklığını-frekansını hesaplar ve anahtarkelime:sıklık tipinde
    #bir dictionarye atar.
    
    frequencies = {}
    counter = 0
    
    for word in data:
        for index in list(dictionaryDataset.keys()):
            for words in index.split():
                if(word == words):
                    counter+=1
            
        try:
            frequencies.update({word:1+np.log(len(dictionaryDataset)/counter)})
            
        except:
            frequencies.update({word:1})
            
        counter = 0
        
    return frequencies


def getScore(frequenciesData,DocumentFrequency): #üstteki iki fonksiyonun sonuçları üzerinden her bir input key'i için skor değerleri üretir.
    
    newDict = {}
 
    for index in frequenciesData.keys():
        newDict.update({index:DocumentFrequency[index]})
        newDict[index] = DocumentFrequency[index] * frequenciesData[index]
        
        
        
    return newDict       

def getCosineSimilarity(resultList): #input keyler ile datasetteki tüm keylerinin skorlarını karşılaştırır, input key'e en yakın skora sahip olan key in index değerini döndürür
    #bu index değeri ile chatbot un vereceği cevaba ulaşılır.
    
   
    cosine = 0
    max_cosine = -1
    index_result = 0
    
    for i in range(len(resultList) - 1):
        
        cosine = np.dot(resultList[0],resultList[i+1]) / (  np.sqrt(np.sum(np.square(resultList[0]))) * np.sqrt(np.sum(np.square(resultList[i+1])))  )
        
        if cosine > max_cosine:
            index_result = i
            max_cosine = cosine
            
            
            
    return index_result
        
        
        
if __name__ == "__main__":
    
    
    nltk.download('stopwords')
    nltk.download('wordnet')
    stop_words = set(stopwords.words('english'))

    lemmatizer = WordNetLemmatizer() 


    while True:
        pipe = win32pipe.CreateNamedPipe(
        r'\\.\pipe\Chatbox',
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0,
        None)
        
        
        print("waiting for client")
        win32pipe.ConnectNamedPipe(pipe, None)
        print("got client")

      
        data = win32file.ReadFile(pipe,4096)
        getStr = str(data[1])
        endIndex = getStr[2:].find("\\")
            
        sentence = getStr[2:endIndex+2]
        print(sentence)
    
        dictionaryDataset = {}
        
        a_file = open("sample.csv", "r")
      
    ###################################################################################### Inputu anahtar kelimelere dönüştürmek için gerekli nesneler
        reader = csv.reader(a_file)  #Veriyi oku
        for key in reader:
                if(len(key)>0):
                    dictionaryDataset.update({key[0] : key[1]}) #veriyi dictionary yapısına dönüştür
    
        a_file.close() #Dosyayı kapat
    
        
        BagOfWords = createBagOfWords(sentence) #Inputtan anahtar kelimeleri al
            
        
        frequenciesData = termFrequency(BagOfWords,BagOfWords)
        DocumentFrequency = InverseDocumentFrequency(BagOfWords,dictionaryDataset)
        result = getScore(frequenciesData,DocumentFrequency)
        
        
        resultList = []
        resultList.append(np.array(list(result.values())))
        
        
        for index in dictionaryDataset.keys(): #Dosyadaki her bir anahtar kelime ve karşılıkları için hesaplamaları yapar
            
             frequenciesData = termFrequency(BagOfWords,list(index.split(" ")))
             DocumentFrequency = InverseDocumentFrequency(BagOfWords,dictionaryDataset)
             result = getScore(frequenciesData,DocumentFrequency)
             resultList.append(np.array(list(result.values())))
         
            
        indexRes = getCosineSimilarity(resultList)
        
        
        print(list(dictionaryDataset.values())[indexRes]) #Cevap burda yazılıyor
        
        if(not dictionaryDataset.get(" ".join(BagOfWords))): #Eğer verilen anahtar kelimeler csv dosyasında yoksa kaydeder
            
            dictionaryDataset.update({sentence:list(dictionaryDataset.values())[indexRes]})
            a_file = open("sample.csv", "a")
            writer = csv.writer(a_file)
        
            writer.writerow([" ".join(BagOfWords),list(dictionaryDataset.values())[indexRes]] )
            a_file.close()
            
        result = str.encode(f"{list(dictionaryDataset.values())[indexRes]}")     
        win32file.WriteFile(pipe, result)    
        win32file.CloseHandle(pipe)
    